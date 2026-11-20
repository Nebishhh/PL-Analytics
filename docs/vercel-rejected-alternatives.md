#### Rejected alternatives (§7.3)

Three alternatives were evaluated and not adopted:

- **Vercel Services** (Beta at the time). Services is Vercel's documented route
  for a Python backend beside another framework, but a service is built from
  its own root. A `backend/` root cannot reach the artefacts in
  `01-value-predictor/`, `02-match-predictor/`, `03-style-finder/` and
  `data/processed/`, and it breaks the package-relative imports
  (`from . import ...`) the backend uses. Moving the artefacts is forbidden by
  §0. A repository-root service was undocumented on where it looks up Python
  dependencies, so it could not be planned against.
- **The FastAPI framework preset** (a root `pyproject.toml` with
  `tool.vercel.entrypoint = "backend.app:app"`). The preset routes every
  request to the app, so the single-page-app fallback for `BrowserRouter`
  routes would have had to be added to `backend/app.py` — a deployment concern
  moved into the backend — and it would have added a root `pyproject.toml`.
- **A root `requirements.txt` containing only `-r backend/requirements.txt`.**
  This was the first version. uv and pip both resolve it, but Vercel's build
  parses the file itself before installing and failed with "Error parsing
  included file ... at position 0". Copying the pins into both files was also
  rejected: two lists of pins will eventually disagree.

The file-based `api/` function with `"framework": null` keeps the backend
unchanged and the deployment surface to the four files above. Revisit if
Services leaves Beta with documented support for shared files outside a
service root.

