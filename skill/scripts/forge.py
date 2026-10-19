"""Look up GitLab / GitHub issues and merge/pull requests via the `glab` / `gh` CLIs.

Works for any host the CLI is logged in to (gitlab.com, self-hosted GitLab,
github.com, GitHub Enterprise). Returns None when the URL is no such item or
the lookup fails, so callers can fall back to plain HTTP.
"""
import json, re, shutil, subprocess, urllib.parse

GITLAB = re.compile(r"https?://([^/\s]+)/([^\s)]+?)/-/(issues|work_items|merge_requests)/(\d+)")
GITHUB = re.compile(r"https?://([^/\s]+)/([^/\s]+/[^/\s]+)/(issues|pull)/(\d+)")


def _api(cli, host, path):
    if not shutil.which(cli):
        return None
    res = subprocess.run([cli, "api", "--hostname", host, path], capture_output=True, text=True)
    if res.returncode != 0:
        return None
    try:
        return json.loads(res.stdout)
    except ValueError:
        return None


def find(text):
    """All issue/MR/PR URLs in text, as (url, host, project, kind, number)."""
    hits = [(m.group(0), *m.groups(), "gitlab") for m in GITLAB.finditer(text)]
    hits += [(m.group(0), *m.groups(), "github") for m in GITHUB.finditer(text) if "/-/" not in m.group(0)]
    return hits


def lookup(url):
    """(ref, title, state) for an issue/MR/PR URL, e.g. ("website#179", "…", "opened"); or None."""
    for _, host, project, kind, num, forge in find(url)[:1]:
        if forge == "gitlab":
            endpoint = "merge_requests" if kind == "merge_requests" else "issues"
            data = _api("glab", host, f"projects/{urllib.parse.quote(project, safe='')}/{endpoint}/{num}")
            sep = "!" if endpoint == "merge_requests" else "#"
            if data:
                return f"{project.split('/')[-1]}{sep}{num}", data.get("title", ""), data.get("state", "")
        else:
            data = _api("gh", host, f"repos/{project}/{'pulls' if kind == 'pull' else 'issues'}/{num}")
            if data:
                state = "merged" if data.get("merged_at") else data.get("state", "")
                return f"{project.split('/')[-1]}#{num}", data.get("title", ""), state
    return None
