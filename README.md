# agent_eval_platform
Demo agent evaluation platform

## Local Demo Dashboard

This repo includes a minimal local dashboard for triggering a GitHub Actions caller workflow via `workflow_dispatch`.

- Backend: Flask (`dashboard/app.py`)
- Frontend: plain HTML/CSS (`dashboard/templates/index.html`, `dashboard/static/style.css`)

### Run locally

1. Install Python 3.11+.
2. Install Flask:

```bash
pip install flask
```

3. Start the app:

```bash
python dashboard/app.py
```

4. Open:

```text
http://127.0.0.1:5000
```

### GitHub token permissions needed

For dispatching a workflow in the target repo and fetching issue details first, use a token that can access both Actions and Issues in that repo.

- Fine-grained PAT (recommended for demo):
  - Repository access to the target repo (`eval_regress_test`)
  - Repository permissions:
    - `Actions: Read and write` (needed for workflow dispatch)
    - `Issues: Read` (needed to fetch issue title/body by issue id)
    - `Contents: Read` (commonly required by workflows)

- Classic PAT (if used):
  - `repo`
  - `workflow`

### How to use the UI

1. Fill in:
   - `GitHub owner`
   - `GitHub repo`
   - `workflow file name or id` (for example: `call-platform-eval.yml`)
   - `branch/ref`
   - all eval input fields (`issue_id`, `model`, `base_commit`, `target_test`, `full_verify`, `source_file`, `prompt_file`)
   - `GitHub token`
2. Click **Dispatch Workflow**.
3. The backend first fetches the GitHub issue (`title + body`) using `issue_id`.
4. It then dispatches the caller workflow with all form inputs plus `issue_description` from the issue.
5. The page shows:
   - raw GitHub API status code
   - success/error message
   - raw response body (if any)

# TODO_DEMO: Current token handling is prototype-only (manual form entry). Replace with GitHub App auth for production.
