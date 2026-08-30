"""AGENTS.md constraints, as executable assertions.

Run with:
    python -m backend.tests.test_constraints

Deliberately dependency-free (no pytest) so it can run anywhere the backend
runs. These are the checks a grep cannot make.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import artefacts as art  # noqa: E402
from backend.config import ROOT  # noqa: E402

FAILURES: list[str] = []


def code_only(source: str) -> str:
    """Source with docstrings and comments blanked out.

    This matters more than it looks. The first version of these checks
    searched raw source and failed on all of match.py, artefacts.py and
    value.py -- every hit was the COMMENT explaining the rule, not a
    violation of it. `predict_proba` appears in match.py because its docstring
    says it must never be called.

    A check that fires on its own rationale is worse than no check: the
    cheapest way to make it pass is to delete the explanation. So the rules are
    enforced against code, and the prose is free to name what it forbids.
    """
    tree = ast.parse(source)
    lines = source.splitlines()
    blank = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            doc = body[0]
            blank.update(range(doc.lineno - 1, (doc.end_lineno or doc.lineno)))
    kept = ["" if i in blank else re.sub(r"#.*$", "", line)
            for i, line in enumerate(lines)]
    return "\n".join(kept)


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def main() -> int:
    a = art.load()
    # Code only: see code_only() for why the raw source is not searched.
    backend_src = {p: code_only(p.read_text(encoding="utf-8"))
                   for p in (ROOT / "backend").rglob("*.py")}

    print("\n--- AGENTS.md 2.1: project 02 never computes a forecast ---")
    match_files = {p: s for p, s in backend_src.items()
                   if "match" in p.name and "test" not in p.name}
    check("no predict_proba in match router",
          not any("predict_proba" in s for s in match_files.values()))
    check("no .predict( in match router",
          not any(re.search(r"\.predict\(", s) for s in match_files.values()))
    check("oof_predictions.csv is the forecast source",
          any("oof" in s.lower() for s in match_files.values()))

    print("\n--- AGENTS.md 1.2: read-only over the artefacts ---")
    for bad in ("joblib.dump", ".to_csv(", ".fit(", ".fit_predict(", "open("):
        offenders = [p.name for p, s in backend_src.items()
                     if bad in s and "test" not in p.name]
        check(f"no {bad!r} anywhere in backend/", not offenders, str(offenders))

    print("\n--- AGENTS.md 2.3: no hardcoded quality figures in routes ---")
    routes = {p: s for p, s in backend_src.items() if "routers" in str(p)}
    # Numbers that must come from an artefact, never typed into route code.
    forbidden = ["0.727", "0.470", "0.446", "0.180", "1.75", "0.966", "0.835",
                 "0.5763", "0.5884"]
    for lit in forbidden:
        offenders = [p.name for p, s in routes.items()
                     if re.search(rf"(?<![\d.]){re.escape(lit)}(?![\d])", s)]
        check(f"literal {lit} absent from routers", not offenders, str(offenders))
    check("threshold 0.10 absent from routers",
          not any(re.search(r"(?<![\d.])0\.10(?![\d])", s) for s in routes.values()))
    check("threshold 0.50 absent from routers",
          not any(re.search(r"(?<![\d.])0\.50(?![\d])", s) for s in routes.values()))

    print("\n--- artefact contents the API depends on ---")
    check("01 has band_coverage", "band_coverage" in a.value)
    check("01 has caveat_thresholds", "caveat_thresholds" in a.value)
    check("02 has cv.baseline_accuracy", "baseline_accuracy" in a.match["cv"])
    check("03 has thresholds", "thresholds" in a.style)
    check("03 has position_adjacent", "position_adjacent" in a.style)

    print("\n--- data invariants ---")
    check("match OOF covers 2,967 of 4,616",
          len(a.match_oof) == 2967 and len(a.match_features) == 4616,
          f"{len(a.match_oof)} / {len(a.match_features)}")
    check("no OOF row for seasons before 2017",
          int(a.match_oof.season.min()) == 2017)
    check("style slugs unique", a.style_assignments.slug.is_unique)
    check("style has 315 players", len(a.style_assignments) == 315)
    check("value list has 661, modelling 498",
          len(a.value_players) == 661 and len(a.value_modelling) == 498)

    print("\n--- position_adjacent matches the Streamlit app's {0, 1} ---")
    adjacent = {int(k) for k, v in a.style["position_adjacent"].items() if v}
    app_src = (ROOT / "03-style-finder" / "app.py").read_text(encoding="utf-8")
    m = re.search(r"POSITION_ADJACENT\s*=\s*\{([^}]*)\}", app_src)
    from_app = {int(x) for x in re.findall(r"\d+", m.group(1))} if m else set()
    check("artefact agrees with app.py", adjacent == from_app,
          f"artefact={adjacent} app={from_app}")

    print("\n--- thresholds match the Streamlit app's constants ---")
    for const, key in (("CONTESTED_MARGIN", "contested_margin"),
                       ("BORDERLINE_MARGIN", "borderline_margin"),
                       ("BORDERLINE_SIL", "borderline_silhouette")):
        m = re.search(rf"^{const}\s*=\s*([\d.]+)", app_src, re.M)
        check(f"{const} matches artefact",
              m is not None and float(m.group(1)) == a.style["thresholds"][key],
              f"app={m.group(1) if m else None} "
              f"artefact={a.style['thresholds'][key]}")

    print(f"\n{'=' * 60}")
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        return 1
    print("all constraint checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
