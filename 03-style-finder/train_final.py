"""
03-style-finder : fit and persist the clustering
================================================
Fits the chosen K-Means model on all 315 players and writes three things:
the fitted pipeline, the per-player cluster assignments, and the generated
cluster names.

Separate from cluster.py for the same reason as in projects 01 and 02: that
script explores and answers "which k, and how good is it", this one answers
"give me that model, fitted, on disk". Re-running the exploration never
overwrites the artefact.

WHAT IS BEING PERSISTED, AND WHAT IT IS WORTH
  The honest framing from cluster.py travels with the artefact rather than
  being left behind in a console log. Silhouette at k=4 is 0.180, and no k
  between 2 and 10 exceeds 0.237 -- below the 0.25 line conventionally taken
  as the threshold for meaningful structure. These are regions of a continuous
  distribution, not natural kinds.

  The metadata therefore stores silhouette, the stability ARI, the
  group-normalised agreement ARI and the group variance shares, so any
  consumer of this file can see the weakness without re-deriving it. An app
  that loads this and presents four crisp archetypes would be misrepresenting
  it, and the stored figures are what make that visible.

WHY BOTH A MODEL AND A LABEL TABLE
  Unlike projects 01 and 02, the useful output here is mostly the assignment
  of the 315 known players, not prediction for new ones. The fitted pipeline
  is persisted anyway so a new player's profile can be assigned to a cluster,
  but the label table is what an app would actually read.

  Note what predicting for a new player means: nearest centroid in a 10-D
  standardised space. With silhouette at 0.180 many players sit near a
  boundary, so a "predicted cluster" is a weak statement. distance_to_centroid
  and margin_to_next are stored per player precisely so that closeness to a
  boundary is visible rather than hidden behind a confident label.

CLUSTER NUMBERING IS NOT STABLE ACROSS REFITS
  K-Means labels are arbitrary integers; cluster 0 here may be cluster 2 on a
  refit even with an identical partition. The names are therefore the durable
  identifier, and both the names and the label table are written together from
  the same fit so they cannot disagree.

Reads : data/processed/pl_player_profiles.csv
Writes: 03-style-finder/model.joblib
        03-style-finder/cluster_assignments.csv
"""

import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, silhouette_samples,
                             silhouette_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from cluster import (K_CHOSEN, LABELS, SEED, SEEDS,  # noqa: E402
                     group_variance_shares, load, name_clusters)

MODEL_OUT = Path("03-style-finder/model.joblib")
LABELS_OUT = Path("03-style-finder/cluster_assignments.csv")

# Confidence-tier thresholds. These previously existed only inside app.py,
# which imports Streamlit and therefore cannot be read by anything else, so a
# second consumer had no honest source for them.
#
# The pairing is deliberate and is the reason both are stored rather than just
# the margin. margin_to_next asks whether another centroid is nearly as close
# -- geometry. Per-player silhouette asks whether the player sits closer to
# another cluster's members than to his own -- density. They are near
# independent: only 4 of the 19 negative-silhouette players also have a margin
# under 0.10, so a margin-only rule would present the other 15 as confidently
# assigned.
CONTESTED_MARGIN = 0.10
BORDERLINE_MARGIN = 0.50
BORDERLINE_SILHOUETTE = 0.05


def main() -> None:
    df, feats, groups = load()

    # One Pipeline so scaling travels with the model. A consumer that scaled
    # separately would have to reproduce the training means and standard
    # deviations exactly, and getting that subtly wrong fails silently.
    model = Pipeline([
        ("scale", StandardScaler()),
        ("kmeans", KMeans(n_clusters=K_CHOSEN, n_init=25, random_state=SEED)),
    ])
    labels = model.fit_predict(df[feats])
    z = model.named_steps["scale"].transform(df[feats])

    names = name_clusters(df, feats, labels)

    # Which clusters mostly restate position, computed rather than hardcoded so
    # it stays true if the fit ever changes.
    #
    # The metric is CAPTURE, not purity, and the difference is not cosmetic.
    # Purity asks "what share of this cluster is position X"; capture asks
    # "what share of all position-X players landed in this cluster". The claim
    # being made is that knowing a player's position largely tells you his
    # cluster, which is capture.
    #
    # They disagree here. Cluster 3 is 82.8% midfielders by purity but holds
    # only 34% of the league's midfielders, so knowing someone is a midfielder
    # says little about whether he is in it. A purity rule would wrongly flag
    # it as position-adjacent. Capture at 0.60 reproduces {0, 1} -- cluster 0
    # holds 96.4% of pure forwards, cluster 1 holds 72.9% of pure defenders --
    # which is what the analysis actually found.
    POSITION_CAPTURE = 0.60
    _tmp = df.assign(_c=labels)
    position_adjacent = {
        int(c): bool(max(
            ((_tmp._c == c) & (_tmp.pos == p)).sum() / (_tmp.pos == p).sum()
            for p in _tmp.pos.unique() if (_tmp.pos == p).sum() > 0
        ) >= POSITION_CAPTURE)
        for c in sorted(set(labels))
    }
    assert all(names.values()), "a cluster received an empty name"
    assert len(set(names.values())) == K_CHOSEN, "duplicate cluster names"

    sil_overall = silhouette_score(z, labels)
    sil_per_player = silhouette_samples(z, labels)

    # Stability, recomputed rather than quoted, so the artefact cannot carry a
    # number that no longer holds.
    seed_labels = [
        Pipeline([("scale", StandardScaler()),
                  ("kmeans", KMeans(n_clusters=K_CHOSEN, n_init=10,
                                    random_state=s))]).fit_predict(df[feats])
        for s in range(SEEDS)
    ]
    aris = [adjusted_rand_score(seed_labels[i], seed_labels[j])
            for i in range(SEEDS) for j in range(i + 1, SEEDS)]

    # Group-normalised comparison, also recomputed.
    z_w = z.copy()
    for g, cols in groups.items():
        idx = [feats.index(c) for c in cols]
        z_w[:, idx] /= np.sqrt(len(cols))
    ari_groupnorm = adjusted_rand_score(
        labels, KMeans(n_clusters=K_CHOSEN, n_init=25,
                       random_state=SEED).fit_predict(z_w)
    )

    # --- per-player distances -----------------------------------------------
    # How far each player sits from their own centroid, and how much closer
    # that centroid is than the next one. A small margin means the assignment
    # is close to arbitrary, which at silhouette 0.180 is common.
    centroids = model.named_steps["kmeans"].cluster_centers_
    d = np.linalg.norm(z[:, None, :] - centroids[None, :, :], axis=2)
    order = np.argsort(d, axis=1)
    nearest = np.take_along_axis(d, order, axis=1)

    out = df[["player", "squad", "pos", "age", "minutes"]].copy()
    out["cluster"] = labels
    out["cluster_name"] = [names[c] for c in labels]
    out["distance_to_centroid"] = nearest[:, 0].round(4)
    out["margin_to_next"] = (nearest[:, 1] - nearest[:, 0]).round(4)
    # The second-nearest centroid, named. Without this a consumer can see that
    # an assignment was close but not what it was close TO, which is the more
    # useful half of the statement.
    out["rival_cluster"] = order[:, 1]
    out["rival_cluster_name"] = [names[c] for c in order[:, 1]]
    out["distance_to_rival"] = nearest[:, 1].round(4)
    out["silhouette"] = sil_per_player.round(4)
    for f in feats:
        out[f] = df[f]
    out = out.sort_values(["cluster", "distance_to_centroid"]).reset_index(drop=True)

    LABELS_OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(LABELS_OUT, index=False, encoding="utf-8")

    artefact = {
        "model": model,
        "k": K_CHOSEN,
        "feature_names": list(feats),
        "feature_labels": dict(LABELS),
        "groups": {g: list(c) for g, c in groups.items()},
        "cluster_names": names,
        "cluster_sizes": {int(c): int((labels == c).sum())
                          for c in sorted(names)},
        "cluster_feature_means": df.assign(_c=labels).groupby("_c")[feats]
                                   .mean().round(4).to_dict("index"),
        "quality": {
            "silhouette": round(float(sil_overall), 4),
            "silhouette_note": (
                "Below 0.25, the conventional threshold for meaningful "
                "structure. These are regions of a continuous distribution, "
                "not natural kinds. Do not present them as crisp archetypes."
            ),
            "stability_ari_mean": round(float(np.mean(aris)), 4),
            "stability_ari_min": round(float(min(aris)), 4),
            "groupnorm_ari": round(float(ari_groupnorm), 4),
            "groupnorm_note": (
                "Agreement with a fit that equalises group contribution at "
                "33/33/33 instead of 50/20/30. Roughly one player in six "
                "changes cluster, so individual assignments are less robust "
                "than the overall shape."
            ),
            "group_variance_shares": {
                g: round(s, 2)
                for g, s in group_variance_shares(z, feats, groups).items()
            },
        },
        "thresholds": {
            "contested_margin": CONTESTED_MARGIN,
            "borderline_margin": BORDERLINE_MARGIN,
            "borderline_silhouette": BORDERLINE_SILHOUETTE,
        },
        # Clusters that largely restate a position rather than revealing
        # something new. Derived, not asserted: a cluster qualifies when one
        # position group supplies at least 60% of its members.
        "position_adjacent": position_adjacent,
        "n_players": len(df),
        "trained_on": "pl_player_profiles.csv",
        "trained_date": date.today().isoformat(),
        "sklearn_version": __import__("sklearn").__version__,
    }
    joblib.dump(artefact, MODEL_OUT)

    # --- report --------------------------------------------------------------
    print(f"Fitted K-Means k={K_CHOSEN} on {len(df)} players, "
          f"{len(feats)} features")
    print(f"  silhouette          {sil_overall:.3f}  "
          f"(below 0.25 -- weak structure, stored with the artefact)")
    print(f"  stability ARI       {np.mean(aris):.3f} mean, "
          f"{min(aris):.3f} min across {SEEDS} seeds")
    print(f"  group-normalised    ARI {ari_groupnorm:.3f}")
    print("  group variance      " + ", ".join(
        f"{g.split('_')[0].lower()} {s:.0f}%"
        for g, s in group_variance_shares(z, feats, groups).items()))

    print(f"\nWrote {MODEL_OUT} ({MODEL_OUT.stat().st_size:,} bytes)")
    print(f"Wrote {LABELS_OUT} ({len(out):,} rows x {len(out.columns)} cols)")

    print("\nClusters:")
    for c in sorted(names):
        m = labels == c
        print(f"  {c} (n={m.sum():>3}, sil {sil_per_player[m].mean():+.3f}): "
              f"{names[c]}")

    # --- round trip ----------------------------------------------------------
    reloaded = joblib.load(MODEL_OUT)
    assert np.array_equal(reloaded["model"].predict(df[feats]), labels), \
        "round-trip mismatch"
    print("\nRound-trip load verified.")

    # --- how many assignments are marginal? ---------------------------------
    # The number that matters for anything consuming this file.
    weak = (out.silhouette < 0).sum()
    tight = (out.margin_to_next < 0.5).sum()
    print(f"\nAssignment confidence:")
    print(f"  players with negative silhouette (closer to another cluster's "
          f"members): {weak} of {len(out)} ({weak / len(out) * 100:.0f}%)")
    print(f"  players within 0.5 of a rival centroid: {tight} "
          f"({tight / len(out) * 100:.0f}%)")
    print("  Both are stored per player so a consumer can surface the "
          "uncertainty\n  rather than presenting every label as equally solid.")

    print("\nMost central player per cluster (nearest the centroid):")
    for c in sorted(names):
        r = out[out.cluster == c].iloc[0]
        print(f"  {c}: {r.player} ({r.squad}, {r.pos}) "
              f"d={r.distance_to_centroid:.2f}")


if __name__ == "__main__":
    main()
