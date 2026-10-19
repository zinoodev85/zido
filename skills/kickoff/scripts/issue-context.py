#!/usr/bin/env python3
"""Dump everything a GitLab/GitHub issue, work item, MR or PR says, as Markdown, for writing a kickoff prompt.

Usage: issue-context.py <url> [--images DIR]
  --images DIR  also download images attached to the issue and its comments into DIR
                (named issue-img<N>.<ext>) and list the local paths.

Prints: title, state, labels, milestone, assignees, author, body, every human comment
(system notes dropped), related/linked MRs and issues. Uses `glab` / `gh`, so private
repos on any logged-in host work. Exits 1 when the URL is no issue/MR/PR or the lookup fails.
"""
import json, pathlib, re, shutil, subprocess, sys, urllib.parse

GITLAB = re.compile(r"https?://([^/\s]+)/([^\s)]+?)/-/(issues|work_items|merge_requests)/(\d+)")
GITHUB = re.compile(r"https?://([^/\s]+)/([^/\s]+/[^/\s]+)/(issues|pull)/(\d+)")
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")

args = sys.argv[1:]
url = args[0] if args else ""
img_dir = pathlib.Path(args[args.index("--images") + 1]) if "--images" in args else None
out, images = [], []


def run(cmd, binary=False):
    if not shutil.which(cmd[0]):
        return None
    res = subprocess.run(cmd, capture_output=True, text=not binary)
    return res.stdout if res.returncode == 0 else None


def api(cli, host, path):
    raw = run([cli, "api", "--hostname", host, path])
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def section(title, body):
    if body and body.strip():
        out.extend([f"## {title}", "", body.strip(), ""])


def gitlab(host, project, kind, iid):
    pid = urllib.parse.quote(project, safe="")
    endpoint = "merge_requests" if kind == "merge_requests" else "issues"
    item = api("glab", host, f"projects/{pid}/{endpoint}/{iid}")
    if not item:
        return False
    sep = "!" if endpoint == "merge_requests" else "#"
    out.extend([f"# {project}{sep}{iid}: {item['title']}", ""])
    meta = [f"- State: {item.get('state')}",
            f"- Author: {(item.get('author') or {}).get('name')}",
            f"- Created: {item.get('created_at', '')[:10]}",
            f"- Labels: {', '.join(item.get('labels') or []) or '-'}",
            f"- Milestone: {(item.get('milestone') or {}).get('title', '-')}",
            f"- Assignees: {', '.join(a['name'] for a in item.get('assignees') or []) or '-'}"]
    if endpoint == "merge_requests":
        meta.append(f"- Branch: {item.get('source_branch')} → {item.get('target_branch')}")
    out.extend(meta + [""])
    section("Description", item.get("description"))
    images.extend(IMG.findall(item.get("description") or ""))

    notes = api("glab", host, f"projects/{pid}/{endpoint}/{iid}/notes?per_page=100&sort=asc") or []
    human = [n for n in notes if not n.get("system")]
    if human:
        out.extend(["## Comments", ""])
        for n in human:
            out.extend([f"**{n['author']['name']}** ({n['created_at'][:10]}):", "", n["body"].strip(), ""])
            images.extend(IMG.findall(n["body"]))

    rel = []
    if endpoint == "issues":
        for mr in api("glab", host, f"projects/{pid}/issues/{iid}/related_merge_requests") or []:
            rel.append(f"- MR !{mr['iid']} ({mr['state']}, branch `{mr['source_branch']}`): {mr['title']} {mr['web_url']}")
        for li in api("glab", host, f"projects/{pid}/issues/{iid}/links") or []:
            rel.append(f"- Issue #{li['iid']} ({li['state']}, {li.get('link_type', 'relates_to')}): {li['title']} {li['web_url']}")
    else:
        for issue in api("glab", host, f"projects/{pid}/merge_requests/{iid}/closes_issues") or []:
            rel.append(f"- Closes #{issue['iid']} ({issue['state']}): {issue['title']} {issue['web_url']}")
    section("Related", "\n".join(rel))

    if img_dir and images:
        img_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for n, src in enumerate(images, 1):
            m = re.match(r"^/uploads/([0-9a-f]+)/(.+)$", src)
            data = run(["glab", "api", "--hostname", host, f"projects/{pid}/uploads/{m.group(1)}/{m.group(2)}"],
                       binary=True) if m else None
            if data:
                path = img_dir / f"issue-img{n}{pathlib.Path(m.group(2)).suffix or '.png'}"
                path.write_bytes(data)
                saved.append(f"- {path}")
            else:
                saved.append(f"- not downloaded: {src}")
        section(f"Images ({sum(not x.startswith('- not') for x in saved)} of {len(saved)} downloaded)", "\n".join(saved))
    elif images:
        section("Images", "\n".join(f"- {s}" for s in images))
    return True


def github(host, repo, kind, num):
    fields = "title,state,author,createdAt,labels,milestone,assignees,body,comments"
    cmd = ["gh", "pr" if kind == "pull" else "issue", "view", str(num), "-R", f"{host}/{repo}", "--json",
           fields + (",headRefName,baseRefName,closingIssuesReferences" if kind == "pull" else ",closedByPullRequestsReferences")]
    raw = run(cmd)
    if not raw:
        return False
    item = json.loads(raw)
    out.extend([f"# {repo}#{num}: {item['title']}", "",
                f"- State: {item.get('state')}",
                f"- Author: {(item.get('author') or {}).get('login')}",
                f"- Created: {item.get('createdAt', '')[:10]}",
                f"- Labels: {', '.join(l['name'] for l in item.get('labels') or []) or '-'}",
                f"- Milestone: {(item.get('milestone') or {}).get('title', '-')}",
                f"- Assignees: {', '.join(a['login'] for a in item.get('assignees') or []) or '-'}", ""])
    section("Description", item.get("body"))
    images.extend(IMG.findall(item.get("body") or ""))
    if item.get("comments"):
        out.extend(["## Comments", ""])
        for c in item["comments"]:
            out.extend([f"**{c['author']['login']}** ({c['createdAt'][:10]}):", "", c["body"].strip(), ""])
            images.extend(IMG.findall(c["body"]))
    refs = item.get("closingIssuesReferences") or item.get("closedByPullRequestsReferences") or []
    section("Related", "\n".join(f"- #{r.get('number')} {r.get('url', '')}" for r in refs))
    section("Images", "\n".join(f"- {s}" for s in images))
    return True


m = GITLAB.search(url)
ok = gitlab(*m.groups()) if m else False
if not ok and not m:
    g = GITHUB.search(url)
    ok = github(*g.groups()) if g else False
if not ok:
    sys.exit(1)
print("\n".join(out))
