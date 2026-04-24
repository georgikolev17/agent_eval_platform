from flask import Flask, render_template, request
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

app = Flask(__name__)


def trigger_workflow(owner: str, repo: str, workflow_id_or_file: str, ref: str, token: str, inputs: dict):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id_or_file}/dispatches"
    payload = json.dumps({"ref": ref, "inputs": inputs}).encode("utf-8")

    req = Request(url, data=payload, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=30) as resp:
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
            return status_code, body
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body
    except URLError as e:
        return 0, str(e)


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

    inputs = {
        "issue_id": request.form.get("issue_id", "").strip(),
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
        message = "Dispatch accepted by GitHub Actions."
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
