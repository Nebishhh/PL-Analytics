"""
02-match-predictor : fit and persist the shipping model
=======================================================
Trains HistGradientBoostingClassifier(class_weight="balanced") on all 4,616
matches and writes it to model.joblib.

Separate from model.py for the same reason as in project 01: that script
compares families and answers "which model, and how good is it", this one
answers "give me that model, fitted, on disk". Re-running the comparison
never overwrites the artefact, and the app can never serve something that
was only ever evaluated.

WHY HGB-BALANCED, AND NOT THE MORE ACCURATE MODEL
  Plain logistic regression scores higher on raw accuracy -- 0.512 against
  0.470 -- and it is not the model being shipped.

  It earns that accuracy substantially by declining to predict draws. Its
  draw recall is 0.11: 317 draw predictions across 2,967 test matches, when
  697 draws actually occurred. For an app whose entire purpose is showing a
  Win/Draw/Loss forecast, a model that has quietly reduced the problem to
  two classes is a worse product than a slightly less accurate one that
  attempts all three.

  HGB-balanced has the best macro F1 of the five candidates (0.429), which is
  the metric that refuses to let draw-blindness hide, and it still beats the
  always-home-win baseline on accuracy (+0.024). Draw precision and recall
  are both 0.26 -- modest, but it is genuinely trying.

  This is a deliberate trade of 4.2 accuracy points for a model that answers
  the question actually being asked.

HONEST CEILING
  Max eta-squared across every engineered feature is 0.132: nothing separates
  these classes strongly, and match outcomes are substantially irreducible.
  0.470 against a 0.446 baseline is a real but modest gain, and it is the
  correct result rather than a disappointing one.

DOCUMENTED FUTURE WORK, deliberately not done here
  - HGB hyperparameter tuning. These are library defaults on 4,616 rows and
    are likely leaving something on the table. Any tuning must be nested
    inside the training fold or the CV estimate becomes optimistic.
  - Draws as a distinct problem. An ordinal formulation, or a two-stage
    "decisive vs draw, then which side", may suit them better than flat
    3-class. No configuration tested here found draws: the balanced variants
    only changed how often they guessed, with precision stuck near 0.26.

  Both are separate deliberate steps. Neither is a reason to withhold this
  model, which is at a defensible stopping point.

Reads : data/processed/pl_matches_features.csv
Writes: 02-match-predictor/model.joblib
"""

import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score

sys.path.insert(0, str(Path(__file__).parent))
from model import (CLASSES, CONTEXT_FEATURES, DIFF_FEATURES,  # noqa: E402
                   VENUE_FEATURES, build_xy, make_models, season_splits)

OUT = Path("02-match-predictor/model.joblib")

SHIP = "HGB-bal"

# Measured in model.py under Scheme A (season-based expanding window,
# 9 folds). Stored so the app quotes the cross-validated figures rather than
# anything computed on the training set.
CV = {
    "scheme": "season-based expanding window, 9 folds",
    "accuracy": 0.470, "accuracy_sd": 0.031,
    "macro_f1": 0.429, "macro_f1_sd": 0.028,
    "baseline_accuracy": 0.446,
    "log_loss": 1.158,
    # Per class, summed over folds: precision / recall / F1.
    "per_class": {"H": (0.56, 0.63, 0.59),
                  "D": (0.26, 0.26, 0.26),
                  "A": (0.49, 0.40, 0.44)},
}


def main() -> None:
    x, y, df = build_xy()
    model = make_models()[SHIP]
    model.fit(x, y)

    # In-sample only -- a fit-quality check, NOT a performance claim. The
    # honest numbers are the cross-validated ones in CV above.
    in_sample = accuracy_score(y, model.predict(x))

    artefact = {
        "model": model,
        "model_name": SHIP,
        "classes": list(model.classes_),
        "class_labels": {"H": "Home win", "D": "Draw", "A": "Away win"},
        "feature_names": list(x.columns),
        "diff_features": list(DIFF_FEATURES),
        "venue_features": list(VENUE_FEATURES),
        "context_features": list(CONTEXT_FEATURES),
        "target_order": list(CLASSES),
        "cv": CV,
        "n_training_rows": len(df),
        "seasons": [int(df.season.min()), int(df.season.max())],
        "trained_on": "pl_matches_features.csv",
        "trained_date": date.today().isoformat(),
        "sklearn_version": __import__("sklearn").__version__,
        "handles_nan": True,   # HGB takes NaN natively; no imputer in the pipe
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefact, OUT)

    print(f"Trained {SHIP} on {len(df):,} matches, {x.shape[1]} features")
    print(f"  classes         : {list(model.classes_)}")
    print(f"  in-sample acc   : {in_sample:.3f}  "
          f"(cross-validated is {CV['accuracy']:.3f} -- quote that one)")
    print(f"  CV accuracy     : {CV['accuracy']:.3f} +/- {CV['accuracy_sd']:.3f}"
          f"  (baseline {CV['baseline_accuracy']:.3f})")
    print(f"  CV macro F1     : {CV['macro_f1']:.3f} +/- {CV['macro_f1_sd']:.3f}")
    print(f"  draw P/R/F1     : {CV['per_class']['D']}")
    print(f"\nWrote {OUT} ({OUT.stat().st_size:,} bytes)")

    # Round-trip: an artefact the app cannot load is worse than none.
    reloaded = joblib.load(OUT)
    a = reloaded["model"].predict_proba(x.iloc[:5])
    b = model.predict_proba(x.iloc[:5])
    assert np.allclose(a, b), "round-trip mismatch"
    print("Round-trip load verified.")

    # Confirm the shipped model actually attempts all three classes -- the
    # whole reason it was chosen over the more accurate logistic regression.
    preds = model.predict(x)
    counts = {c: int((preds == c).sum()) for c in CLASSES}
    print(f"\nIn-sample prediction spread: {counts}")
    if counts["D"] == 0:
        raise SystemExit("Shipped model predicts no draws -- defeats the "
                         "reason it was selected.")
    print("Predicts all three classes ✓")

    # And a genuinely out-of-sample spread, since in-sample can flatter.
    tr, te, label = list(season_splits(df))[-1]
    m2 = make_models()[SHIP]
    m2.fit(x.iloc[tr], y[tr])
    oos = m2.predict(x.iloc[te])
    print(f"Held-out season {label}: "
          f"{ {c: int((oos == c).sum()) for c in CLASSES} } "
          f"of {len(te)} matches")


if __name__ == "__main__":
    main()
