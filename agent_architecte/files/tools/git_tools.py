"""
tools/git_tools.py — Git and GitHub tools used by the DevOps agent.
Logs every shell command and its stdout/stderr.
"""

import os
import subprocess
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv
from core.logger import log_tool_call, log_tool_result, log_error

load_dotenv()

GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")


def _run(cmd: list[str], cwd: str) -> tuple[str, str, int]:
    """Run a subprocess command and return (stdout, stderr, returncode)."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.stdout.strip(), proc.stderr.strip(), proc.returncode


@tool
def init_git_repo(repo_path: str) -> str:
    """
    Initialise a local git repository at repo_path.
    Creates the directory if it does not already exist.
    """
    log_tool_call("devops", "init_git_repo", {"repo_path": repo_path})
    try:
        os.makedirs(repo_path, exist_ok=True)

        stdout, stderr, rc = _run(["git", "init"], repo_path)
        if rc != 0:
            raise RuntimeError(stderr)

        # Try creating 'main' branch (newer git) or fall back silently
        _run(["git", "checkout", "-b", "main"], repo_path)

        # Set a default author so commits work without global git config
        _run(["git", "config", "user.email", "agent@sdlc-bot.local"], repo_path)
        _run(["git", "config", "user.name",  "SDLC Agent"], repo_path)

        result = f"✓ Git repo initialised at {repo_path}"
        log_tool_result("init_git_repo", result)
        return result
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def create_github_repo(repo_name: str, description: str) -> str:
    """
    Create a public GitHub repository via the API.
    Returns the HTML URL of the new repository.
    Requires GITHUB_TOKEN and GITHUB_USERNAME in .env.
    """
    log_tool_call("devops", "create_github_repo", {
        "repo_name": repo_name,
        "description": description,
    })
    if not GITHUB_TOKEN:
        result = "SKIPPED (no GITHUB_TOKEN set)"
        log_tool_result("create_github_repo", result, success=False)
        return result
    try:
        resp = requests.post(
            "https://api.github.com/user/repos",
            json={
                "name":        repo_name,
                "description": description,
                "private":     False,
                "auto_init":   False,
            },
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept":        "application/vnd.github.v3+json",
            },
            timeout=15,
        )
        data = resp.json()
        if resp.status_code not in (200, 201):
            raise RuntimeError(data.get("message", resp.text))

        url = data["html_url"]
        log_tool_result("create_github_repo", f"✓ Created: {url}")
        return url
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def git_add_commit(repo_path: str, message: str) -> str:
    """
    Stage all files in repo_path and create a commit with the given message.
    """
    log_tool_call("devops", "git_add_commit", {
        "repo_path": repo_path,
        "message":   message,
    })
    try:
        _run(["git", "add", "."], repo_path)
        stdout, stderr, rc = _run(["git", "commit", "-m", message], repo_path)
        if rc != 0 and "nothing to commit" not in stderr:
            raise RuntimeError(stderr)
        result = f"✓ Committed: {message}"
        log_tool_result("git_add_commit", result)
        return result
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def git_push(repo_path: str, remote_url: str) -> str:
    """
    Add a remote origin (if not already set) and push main to GitHub.
    remote_url should be an HTTPS URL containing the token, e.g.
    https://<token>@github.com/<user>/<repo>.git
    """
    log_tool_call("devops", "git_push", {
        "repo_path":  repo_path,
        "remote_url": remote_url[:40] + "…",
    })
    try:
        # Remove existing origin to avoid 'already exists' error
        _run(["git", "remote", "remove", "origin"], repo_path)
        _run(["git", "remote", "add", "origin", remote_url], repo_path)

        stdout, stderr, rc = _run(
            ["git", "push", "-u", "origin", "main", "--force"], repo_path
        )
        if rc != 0:
            raise RuntimeError(stderr)

        result = f"✓ Pushed to {remote_url.split('@')[-1]}"
        log_tool_result("git_push", result)
        return result
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def git_status(repo_path: str) -> str:
    """Return the current git status of the repository."""
    log_tool_call("devops", "git_status", {"repo_path": repo_path})
    try:
        stdout, stderr, _ = _run(["git", "status", "--short"], repo_path)
        log_tool_result("git_status", stdout or "(clean)")
        return stdout or "(nothing to report)"
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"
