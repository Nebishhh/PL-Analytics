"""
01-value-predictor : fit and persist the shipping model
=======================================================
Trains the model chosen in model.py on all 498 rows and writes it to
model.joblib for the Streamlit app to load.

This is deliberately separate from model.py. That script compares Linear,
Ridge and Lasso under cross-validation and answers "which model, and how
good is it"; this one answers "give me that model, fitted, on disk". Keeping
them apart means the app can never accidentally ship a model that was only
ever evaluated, and re-running the comparison never overwrites the artefact.

Why plain LinearRegression: under 5-fold CV the three candidates land within
0.001 R^2 of each other (0.727 / 0.726 / 0.727), far inside the +/- 0.054
fold noise. Ridge selects alpha ~= 0.17 and Lasso zeroes no coefficients --
both are declining to regularise, because the pathological low-minutes rows
that made regularisation useful are excluded by the 900-minute threshold in
clean.py. Given that, the simplest model wins.

The feature construction is imported from model.py rather than duplicated.
A silent divergence between training and serving column order would produce
confidently wrong predictions with no error, so there is exactly one
definition of it.

Reads : data/processed/pl_player_values.csv
Writes: 01-value-predictor/model.joblib
"""

import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# model.py lives alongside this file; reuse its design-matrix builder and its
# model definitions, so the coverage figure below is measured on exactly the
# model that ships rather than a re-declared copy of it.
sys.path.insert(0, str(Path(__file__).parent))
from model import NUMERIC, N_SPLITS, SEED, build_xy, make_models  # noqa: E402

DATA = Path("data/processed/pl_player_values.csv")
OUT = Path("01-value-predictor/model.joblib")

# Reported to the user as a multiplicative interval rather than a single
# figure. exp(mean CV MAE in log space) is 1.75-1.76 depending on how the
# folds fall, i.e. the typical prediction is out by roughly this factor in
# either direction. Held at 1.75 rather than chased to three digits -- the
# quantity itself moves more than that between fold assignments.
ERROR_FACTOR = 1.75

# Mirrors MIN_PL_MINUTES in clean.py. Stored in the artefact so the app can
# enforce the same rule without hardcoding it in a third place.
MIN_PL_MINUTES = 900

# Thresholds that decide which caveats a player triggers. These previously
# existed only inside app.py, which imports Streamlit and therefore cannot be
# read by anything else -- so a second consumer had no honest source for them
# and would have had to re-declare them. Stored here for the same reason
# min_pl_minutes is: a rule enforced in two places will eventually be enforced
# differently in each.
#
# VETERAN_AGE      the fitted age^2 curve keeps falling past 40 while real
#                  values floor around EUR300-500k, so predictions for the
#                  oldest players are systematically low.
# BLIND_SPOT_POS   positions the model prices almost entirely on goals and
#                  assists, and therefore under-values.
VETERAN_AGE = 38
BLIND_SPOT_POSITIONS = ("Goalkeeper", "Defender")


def band_coverage(x, y, model) -> dict:
    """How often the actual value actually lands inside the +/-1.75x band.

    This exists because the band invites being read as a confidence interval.
    It is not one: it is the typical size of a miss, and a substantial minority
    of players fall outside it. Quoting that share is the only thing that stops
    the range being over-trusted, so it belongs in the artefact rather than
    being recomputed -- or worse, approximated -- by whatever happens to be
    displaying it.

    Two figures, because they are not the same claim:

      in_sample    Measured with the shipped model predicting the rows it was
                   fitted on. This is how the Streamlit app's caption was
                   originally produced, and it is kept so that figure stays
                   traceable to its source.

      out_of_fold  Each player predicted by a model trained without them,
                   under the same 5-fold scheme that produced the headline
                   R^2. This is the honest one and the one a UI should quote.

    The gap here is small -- roughly one point, twelve players -- unlike
    project 02, where the equivalent distinction was 0.980 against 0.470. It
    is recorded anyway, because a coverage rate presented to a reader as "the
    value lands in here N% of the time" is a claim about unseen players, and
    an in-sample measurement cannot support that claim however close it lands.
    """
    actual = np.exp(y)

    inside_in = ((actual >= np.exp(model.predict(x)) / ERROR_FACTOR)
                 & (actual <= np.exp(model.predict(x)) * ERROR_FACTOR))

    oof = np.zeros_like(y)
    for train_idx, test_idx in KFold(n_splits=N_SPLITS, shuffle=True,
                                     random_state=SEED).split(x):
        fold = make_models()["Linear"]
        fold.fit(x.iloc[train_idx], y[train_idx])
        oof[test_idx] = fold.predict(x.iloc[test_idx])
    pred_oof = np.exp(oof)
    inside_oof = ((actual >= pred_oof / ERROR_FACTOR)
                  & (actual <= pred_oof * ERROR_FACTOR))

    return {
        "in_sample": round(float(inside_in.mean()), 4),
        "out_of_fold": round(float(inside_oof.mean()), 4),
        "n": int(len(actual)),
        "method": (f"actual within [prediction / {ERROR_FACTOR}, "
                   f"prediction * {ERROR_FACTOR}]"),
        "cv_scheme": f"{N_SPLITS}-fold, seed {SEED}",
        "quote_this": "out_of_fold",
    }


def main() -> None:
    df = pd.read_csv(DATA, encoding="utf-8")
    x, y = build_xy(df, age_squared=True)

    model = Pipeline([
        ("scale", StandardScaler()),
        ("reg", LinearRegression()),
    ])
    model.fit(x, y)

    # In-sample only -- this is a fit-quality sanity check, NOT a performance
    # claim. The honest number is the cross-validated 0.727 +/- 0.054 from
    # model.py; a full-data R^2 is optimistic by construction.
    in_sample_r2 = model.score(x, y)
    coverage = band_coverage(x, y, model)

    artefact = {
        "model": model,
        "feature_names": list(x.columns),
        "numeric_features": list(NUMERIC),
        "target": "log(market_value_in_eur)",
        "error_factor": ERROR_FACTOR,
        "min_pl_minutes": MIN_PL_MINUTES,
        "n_training_rows": len(df),
        "cv_r2_mean": 0.727,
        "cv_r2_std": 0.054,
        # How often the band actually contains the value. See band_coverage().
        "band_coverage": coverage,
        # Caveat thresholds, so a consumer never re-declares them.
        "caveat_thresholds": {
            "veteran_age": VETERAN_AGE,
            "blind_spot_positions": list(BLIND_SPOT_POSITIONS),
        },
        "trained_on": DATA.name,
        "trained_date": date.today().isoformat(),
        "sklearn_version": __import__("sklearn").__version__,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefact, OUT)

    print(f"Trained plain LinearRegression on {len(df):,} rows, "
          f"{len(x.columns)} features")
    print(f"  features: {', '.join(x.columns)}")
    print(f"  in-sample R^2 {in_sample_r2:.3f}  "
          f"(cross-validated is 0.727 +/- 0.054 -- quote that one)")
    print(f"  error factor x{ERROR_FACTOR}, "
          f"min minutes {MIN_PL_MINUTES}")
    print(f"  band coverage   : {coverage['out_of_fold']:.3f} out-of-fold "
          f"(quote this), {coverage['in_sample']:.3f} in-sample")
    print(f"\nWrote {OUT} ({OUT.stat().st_size:,} bytes)")

    # Round-trip check: a saved model the app cannot load is worse than no
    # saved model, so fail here rather than in the app.
    reloaded = joblib.load(OUT)
    check = reloaded["model"].predict(x.iloc[:5])
    assert np.allclose(check, model.predict(x.iloc[:5])), "round-trip mismatch"
    print("Round-trip load verified.")


if __name__ == "__main__":
    main()
