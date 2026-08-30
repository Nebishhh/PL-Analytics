"""Load the three committed artefacts once, read-only, and normalise them.

AGENTS.md section 1.2: this module opens artefacts with joblib.load and
pandas.read_csv and nothing else. There is no joblib.dump, no .to_csv, no
.fit, and no write handle anywhere under backend/. The models are never
retrained and the files are never modified.

THE NORMALISATION PROBLEM
  The three artefacts store their quality figures in three different shapes,
  because they were written months apart:

    01  flat keys        cv_r2_mean, cv_r2_std
    02  nested dict      cv = {accuracy, accuracy_sd, ...}
    03  nested dict      quality = {silhouette, stability_ari_mean, ...}

  API.md section 3(a) requires the backend to absorb that difference rather
  than rewrite the artefacts to match. Three explicit adapters below do it --
  three rather than one generic flattener, because the shapes genuinely differ
  and a generic one would hide that behind a clever loop.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import joblib
import numpy as np
import pandas as pd

from . import config


# --- slug identity for project 03 --------------------------------------------

# NFKD decomposes accents -- e-acute and o-umlaut reduce to e and o -- but
# these are distinct letters, not decorated ones, so it drops them entirely.
# Without the map "Jorgen" (with a slashed o) slugs to "jrgen".
_TRANSLITERATE = str.maketrans({
    "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "å": "a", "Å": "A",
    "ß": "ss", "đ": "d", "Đ": "D", "ð": "d", "Ð": "D",
    "ł": "l", "Ł": "L", "þ": "th", "Þ": "TH", "œ": "oe", "Œ": "OE",
})


def _slugify(text: str) -> str:
    """ASCII slug. 48 of the 315 names carry non-ASCII characters."""
    norm = unicodedata.normalize("NFKD", text.translate(_TRANSLITERATE))
    ascii_only = norm.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _build_slugs(names: pd.Series, squads: pd.Series) -> list[str]:
    """Stable per-player ids for project 03, which has no id column.

    Three players appear twice in the 315 -- Antoine Semenyo, Jorgen Strand
    Larsen and Marc Guehi, each following a mid-season transfer -- so a name
    alone is genuinely ambiguous, not merely ugly. The squad is appended only
    where a name collides, so the common case stays readable.

    These are served by the listing endpoint. Clients must use what they are
    given rather than constructing slugs themselves, so that this rule can
    change without breaking them.
    """
    counts = names.value_counts()
    return [
        _slugify(f"{n}-{s}") if counts[n] > 1 else _slugify(n)
        for n, s in zip(names, squads)
    ]


# --- registry -----------------------------------------------------------------

@dataclass(frozen=True)
class Artefacts:
    value: dict
    match: dict
    style: dict

    value_players: pd.DataFrame
    value_modelling: pd.DataFrame
    match_features: pd.DataFrame
    match_oof: pd.DataFrame
    style_assignments: pd.DataFrame

    match_oof_index: dict[int, dict] = field(default_factory=dict)
    style_by_slug: dict[str, int] = field(default_factory=dict)


_EXPECTED = {
    "value": ("model", "feature_names", "error_factor", "min_pl_minutes",
              "band_coverage", "caveat_thresholds", "cv_r2_mean", "cv_r2_std"),
    "match": ("model", "cv", "class_labels", "target_order"),
    "style": ("model", "cluster_names", "cluster_sizes", "quality",
              "thresholds", "position_adjacent", "feature_labels", "groups"),
}


def load() -> Artefacts:
    """Called once, from the FastAPI lifespan handler."""
    value = joblib.load(config.VALUE_MODEL)
    match = joblib.load(config.MATCH_MODEL)
    style = joblib.load(config.STYLE_MODEL)

    # Fail loudly at startup rather than 500-ing per request on a missing key.
    for name, art in (("value", value), ("match", match), ("style", style)):
        missing = [k for k in _EXPECTED[name] if k not in art]
        if missing:
            raise RuntimeError(
                f"{name} artefact is missing {missing}. Re-run its "
                f"train_final.py, or the backend is pointed at a stale file."
            )

    value_players = pd.read_csv(config.VALUE_PLAYERS, encoding="utf-8")
    value_modelling = pd.read_csv(config.VALUE_MODELLING, encoding="utf-8")
    match_features = pd.read_csv(config.MATCH_FEATURES, encoding="utf-8",
                                 parse_dates=["date"])
    # Loaded once here, never per request (AGENTS.md section 2.1).
    match_oof = pd.read_csv(config.MATCH_OOF, encoding="utf-8")
    style_assignments = pd.read_csv(config.STYLE_ASSIGNMENTS, encoding="utf-8")

    style_assignments = style_assignments.assign(
        slug=_build_slugs(style_assignments["player"], style_assignments["squad"])
    )
    if style_assignments["slug"].duplicated().any():
        dupes = style_assignments.loc[
            style_assignments["slug"].duplicated(keep=False), "slug"].tolist()
        raise RuntimeError(f"slug collision after disambiguation: {dupes}")

    return Artefacts(
        value=value, match=match, style=style,
        value_players=value_players,
        value_modelling=value_modelling,
        match_features=match_features,
        match_oof=match_oof,
        style_assignments=style_assignments,
        match_oof_index={int(r.game_id): r._asdict()
                         for r in match_oof.itertuples(index=False)},
        style_by_slug={s: i for i, s in
                       enumerate(style_assignments["slug"])},
    )


# --- quality adapters ---------------------------------------------------------
# One per tool. Each reads only from its artefact; no figure originates here.

def value_quality(a: dict) -> dict:
    """01 stores cv_r2_* flat. Flattened shape in, uniform shape out."""
    return {
        "cv_scheme": "5-fold",
        "cv_r2_mean": a["cv_r2_mean"],
        "cv_r2_std": a["cv_r2_std"],
        "error_factor": a["error_factor"],
        "band_coverage": a["band_coverage"],
    }


def match_quality(a: dict) -> dict:
    """02 already nests under `cv`; passed through with per-class reshaped."""
    cv = a["cv"]
    return {
        "cv_scheme": cv["scheme"],
        "accuracy": cv["accuracy"],
        "accuracy_sd": cv["accuracy_sd"],
        "macro_f1": cv["macro_f1"],
        "macro_f1_sd": cv["macro_f1_sd"],
        "baseline_accuracy": cv["baseline_accuracy"],
        "log_loss": cv["log_loss"],
        "per_class": {
            k: {"precision": v[0], "recall": v[1], "f1": v[2]}
            for k, v in cv["per_class"].items()
        },
    }


def style_quality(a: dict) -> dict:
    """03 already nests under `quality`; passed through unchanged."""
    q = a["quality"]
    return {
        # k and n_players sit at the artefact's top level rather than under
        # `quality`, but they are part of the headline any consumer needs to
        # state the result ("k = 4, 315 players"), so they are lifted in here.
        # Previously only the style router added n_players, which meant
        # /api/meta and /api/style/meta disagreed about the shape of the same
        # block -- exactly the drift §2.3 exists to prevent.
        "k": int(a["k"]),
        "n_players": int(a["n_players"]),
        "silhouette": q["silhouette"],
        "silhouette_note": q["silhouette_note"],
        "stability_ari_mean": q["stability_ari_mean"],
        "stability_ari_min": q["stability_ari_min"],
        "groupnorm_ari": q["groupnorm_ari"],
        "groupnorm_note": q["groupnorm_note"],
        "group_variance_shares": q["group_variance_shares"],
    }


# --- project 01 inference -----------------------------------------------------

def value_design_row(row: pd.Series, feature_names: list[str]) -> pd.DataFrame:
    """One player -> one row of the design matrix, in training column order.

    Reindexed onto feature_names from the artefact rather than built in a
    hand-written order: scikit-learn matches on position, so a divergence
    would mispredict silently with no error.
    """
    values = {
        "age": row["age"],
        "pl_matches": row["pl_matches"],
        "pl_minutes": row["pl_minutes"],
        "pl_goals": row["pl_goals"],
        "pl_assists": row["pl_assists"],
        "pl_yellow_cards": row["pl_yellow_cards"],
        "pl_red_cards": row["pl_red_cards"],
        "goals_per90": row["goals_per90"],
        "assists_per90": row["assists_per90"],
        "age_sq": row["age"] ** 2,
        f"pos_{row['position']}": 1.0,
    }
    return pd.DataFrame([values]).reindex(columns=feature_names, fill_value=0.0)


def value_estimate_eur(art: Artefacts, row: pd.Series) -> float:
    """Point estimate in EUR. The model predicts log value."""
    x = value_design_row(row, art.value["feature_names"])
    return float(np.exp(art.value["model"].predict(x)[0]))
