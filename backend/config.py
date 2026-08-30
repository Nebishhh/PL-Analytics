"""Paths and non-model configuration.

Deliberately thin. Every model figure, threshold and label lives in an
artefact and is read at startup -- see artefacts.py. If a number appears in
this file that describes the models rather than the deployment, it is in the
wrong place (AGENTS.md section 2.3).
"""

from pathlib import Path

# Repository root, resolved from this file so the backend can be started from
# any working directory.
ROOT = Path(__file__).resolve().parent.parent

VALUE_DIR = ROOT / "01-value-predictor"
MATCH_DIR = ROOT / "02-match-predictor"
STYLE_DIR = ROOT / "03-style-finder"
PROCESSED = ROOT / "data" / "processed"

# --- artefacts, all read-only -------------------------------------------------
VALUE_MODEL = VALUE_DIR / "model.joblib"
MATCH_MODEL = MATCH_DIR / "model.joblib"
STYLE_MODEL = STYLE_DIR / "model.joblib"

# The 661-row table backs the player list; the 498-row table is what the model
# was fitted on. Both are needed: a player between the two is real, selectable,
# and refused.
VALUE_PLAYERS = PROCESSED / "pl_player_values_prethreshold.csv"
VALUE_MODELLING = PROCESSED / "pl_player_values.csv"

MATCH_FEATURES = PROCESSED / "pl_matches_features.csv"
# The only permitted source of a match forecast. See AGENTS.md section 2.1.
MATCH_OOF = MATCH_DIR / "oof_predictions.csv"

STYLE_ASSIGNMENTS = STYLE_DIR / "cluster_assignments.csv"

# Committed plot PNGs, served as static files rather than regenerated, so the
# methodology pages cannot drift from what the README's claims rest on.
PLOT_DIRS = {"01": VALUE_DIR / "plots",
             "02": MATCH_DIR / "plots",
             "03": STYLE_DIR / "plots"}

# --- deployment ---------------------------------------------------------------
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
API_PREFIX = "/api"
