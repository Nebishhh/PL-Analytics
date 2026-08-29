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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# model.py lives alongside this file; reuse its design-matrix builder.
sys.path.insert(0, str(Path(__file__).parent))
from model import NUMERIC, build_xy  # noqa: E402

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
    print(f"\nWrote {OUT} ({OUT.stat().st_size:,} bytes)")

    # Round-trip check: a saved model the app cannot load is worse than no
    # saved model, so fail here rather than in the app.
    reloaded = joblib.load(OUT)
    check = reloaded["model"].predict(x.iloc[:5])
    assert np.allclose(check, model.predict(x.iloc[:5])), "round-trip mismatch"
    print("Round-trip load verified.")


if __name__ == "__main__":
    main()
