from flask import Flask, render_template, request
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

app = Flask(__name__)


def github_json_request(method: str, url: str, token: str, payload: dict | None = None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if payload is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=30) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body
    except URLError as e:
        return 0, str(e)


def fetch_issue_description(owner: str, repo: str, issue_id: str, token: str):
    issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_id}"
    status_code, body = github_json_request("GET", issue_url, token)

    if status_code != 200:
        return False, status_code, body, "Failed to fetch issue details from GitHub."

    try:
        issue = json.loads(body)
    except json.JSONDecodeError:
        return False, status_code, body, "Issue fetch returned non-JSON response."

    title = (issue.get("title") or "").strip()
    description = (issue.get("body") or "").strip()

    # TODO_DEMO: Replace this simple concatenation with structured issue-to-task mapping if needed.
    combined = f"{title}\n\n{description}".strip()
    return True, status_code, body, combined


def trigger_workflow(owner: str, repo: str, workflow_id_or_file: str, ref: str, token: str, inputs: dict):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id_or_file}/dispatches"
    return github_json_request("POST", url, token, payload={"ref": ref, "inputs": inputs})


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/dispatch")
def dispatch():
    owner = request.form.get("owner", "").strip()
    repo = request.form.get("repo", "").strip()
    workflow_id_or_file = request.form.get("workflow", "").strip()
    ref = request.form.get("ref", "main").strip() or "main"
    token = request.form.get("token", "").strip()
    issue_id = request.form.get("issue_id", "").strip()

    ok, issue_status, issue_raw, issue_payload_or_message = fetch_issue_description(
        owner=owner,
        repo=repo,
        issue_id=issue_id,
        token=token,
    )

    if not ok:
        return render_template(
            "index.html",
            result={
                "status_code": issue_status,
                "message": issue_payload_or_message,
                "response": issue_raw,
            },
            form_values=request.form,
        )

    issue_description = issue_payload_or_message

    inputs = {
        "issue_id": issue_id,
        "issue_description": issue_description,
        "model": request.form.get("model", "").strip(),
        "base_commit": request.form.get("base_commit", "").strip(),
        "target_test": request.form.get("target_test", "").strip(),
        "full_verify": request.form.get("full_verify", "").strip(),
        "source_file": request.form.get("source_file", "").strip(),
        "prompt_file": request.form.get("prompt_file", "").strip(),
    }

    status_code, response_body = trigger_workflow(
        owner=owner,
        repo=repo,
        workflow_id_or_file=workflow_id_or_file,
        ref=ref,
        token=token,
        inputs=inputs,
    )

    if status_code == 204:
        message = "Dispatch accepted by GitHub Actions. Issue description was fetched and passed as input."
    elif status_code == 0:
        message = "Network error while calling GitHub API."
    else:
        message = "GitHub API returned an error."

    return render_template(
        "index.html",
        result={
            "status_code": status_code,
            "message": message,
            "response": response_body,
        },
        form_values=request.form,
    )


if __name__ == "__main__":
    # TODO_DEMO: Prototype only. Replace token-from-form approach with GitHub App auth.
    app.run(host="127.0.0.1", port=5000, debug=True)
