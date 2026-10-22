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
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import artefacts as art  # noqa: E402
from backend.config import ROOT  # noqa: E402
from backend.routers import match as match_router  # noqa: E402

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


# Methods only a classifier has. The match model is the only classifier the
# backend loads, so none of these has a legitimate caller.
CLASSIFIER_METHODS = {"predict_proba", "predict_log_proba", "decision_function",
                      "staged_predict", "staged_predict_proba"}
# The only artefacts whose model may be called (AGENTS.md 2.2).
PREDICTING_ARTEFACTS = {"value", "style"}


def _artefact_model(node: ast.AST) -> str | None:
    """'value' for `<x>.value["model"]`, 'match' for `match["model"]`, etc."""
    if not (isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == "model"):
        return None
    base = node.value
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Name):
        return base.id
    return None


def match_model_violations(source: str) -> list[str]:
    """Every way this source could put the match model to work.

    The older check searched only files named after the match router, so a
    predict_proba call added anywhere else in backend/ passed. Searching every
    file for `.predict(` is not the answer either, because the value route
    legitimately predicts. So the rule is stated about the match model itself,
    on the AST, which also keeps prose out of it (AGENTS.md 7.1):

      1. No classifier-only method is called, on anything.
      2. `.predict(` is called only on `<x>.value["model"]` or
         `<x>.style["model"]`, written out, so an alias cannot launder it.
      3. The match artefact's "model" key is never read, by subscript or .get.
      4. joblib is imported only by artefacts.py, so nothing loads a second
         copy of the match model (checked by the caller, which knows the path).
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method, receiver = node.func.attr, node.func.value
            if method in CLASSIFIER_METHODS:
                found.append(f"line {node.lineno}: .{method}(")
            elif (method == "predict"
                  and _artefact_model(receiver) not in PREDICTING_ARTEFACTS):
                found.append(f"line {node.lineno}: .predict( on something "
                             f"other than the value or style model")
            elif (method == "get" and node.args
                  and isinstance(node.args[0], ast.Constant)
                  and node.args[0].value == "model"
                  and getattr(receiver, "attr", getattr(receiver, "id", None))
                  == "match"):
                found.append(f"line {node.lineno}: match.get(\"model\")")
        elif _artefact_model(node) == "match":
            found.append(f"line {node.lineno}: match[\"model\"]")
    return found


def imports_joblib(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(
                n.name.split(".")[0] == "joblib" for n in node.names):
            return True
        if (isinstance(node, ast.ImportFrom) and node.module
                and node.module.split(".")[0] == "joblib"):
            return True
    return False


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

    print("\n--- AGENTS.md 2.1: the match model predicts nowhere in backend/ "
          "or api/ ---")
    served = [p for p in (ROOT / "backend").rglob("*.py")
              if "tests" not in p.relative_to(ROOT).parts]
    served.append(ROOT / "api" / "index.py")
    raw_src = {p: p.read_text(encoding="utf-8") for p in served}
    uses = {p.relative_to(ROOT).as_posix(): match_model_violations(s)
            for p, s in raw_src.items()}
    uses = {p: v for p, v in uses.items() if v}
    check(f"match model never used for prediction ({len(served)} files)",
          not uses, str(uses))
    loaders = sorted(p.relative_to(ROOT).as_posix()
                     for p, s in raw_src.items() if imports_joblib(s))
    check("joblib imported only by backend/artefacts.py",
          loaders == ["backend/artefacts.py"], str(loaders))

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

    print("\n--- 02 top pick comes from the stored, unrounded probabilities ---")
    # The route is called directly with a stand-in request: it only reads
    # request.app.state.artefacts, and this keeps the file free of httpx.
    request = SimpleNamespace(app=SimpleNamespace(
        state=SimpleNamespace(artefacts=a)))
    # Rounded to 4 dp, H and D both read 0.4628 here; unrounded, D is ahead.
    # The Streamlit app picks from the unrounded values and says draw.
    res = match_router.held_out_forecast(request, 2872394)
    check("game 2872394 top pick is D",
          res.forecast is not None and res.forecast.top_pick == "D",
          f"got {res.forecast.top_pick if res.forecast else None}")
    check("game 2872394 is still served from OOF",
          res.source == "precomputed_out_of_fold"
          and res.computed_at_request_time is False)
    mismatched = []
    for game_id, row in a.match_oof_index.items():
        stored = {k: row[f"p_{k}"] for k in a.match["target_order"]}
        got = match_router.held_out_forecast(request, game_id).forecast
        if got.top_pick != max(stored, key=stored.get):
            mismatched.append(game_id)
    check("top pick matches the stored argmax for every OOF match",
          not mismatched, f"{len(mismatched)} differ: {mismatched[:5]}")

    print(f"\n{'=' * 60}")
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        return 1
    print("all constraint checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
