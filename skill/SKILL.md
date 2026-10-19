---
name: todo
description: Add, list, update or complete the user's todo items (stored in $TODO_HOME, default ~/todos, usable from any directory). Each todo is its own folder (todo.md + images + attachments) under todos/open or todos/done, and TODO.md is a generated index. Use when the user says "/todo", "/todo now …" (add + start a session on it at once), "add a todo", "remember to", "todo done", "what's up next", or pastes a screenshot/image that belongs to a task.
---

# Todos

Data lives in `$TODO_HOME` (default `~/todos`), a git repo. All `todos/…` and `TODO.md` paths below are relative to it — use absolute paths, whatever the current directory is. `<scripts>` = the `scripts/` folder next to this file (`~/.claude/skills/todo/scripts/`). File links in replies: absolute `file://` paths.

Write todos in the language the user writes in. If `$TODO_HOME` has no git repo yet, run `zido init` (or `git init` there) first.

## Layout

```
todos/
  open/<YYYY-MM-DD>-<slug>/
    todo.md          # frontmatter + description
    img1.png …       # images, referenced from todo.md
    email1.md …      # saved emails / long texts, linked from todo.md
  done/<same folder name>/   # moved here when completed
TODO.md              # generated index (due soon, then by project) — never edit by hand
```

`todo.md` format:

```markdown
---
title: Short imperative title
project: website          # area/project; reuse an existing value if one fits
priority: normal          # high | normal | low
created: 2026-10-06
due:                      # optional, YYYY-MM-DD
done:                     # set when completed
zidev:                    # checkout dir of the session working on it (set by Start)
tags: []
---

What needs doing, context, links.

![img1](img1.png)

## Links
- [website#179: Checkout fails without a time slot](https://gitlab.com/acme/website/-/issues/179)

## Attachments
- [Mail from Sam: release planning](email1.md)

## Notes
- 2026-10-06: …
```

## Add

1. Derive title, project, priority, due, tags from the request. Look at existing projects first (`grep -h '^project:' $TODO_HOME/todos/*/*/todo.md | sort -u`) and reuse a matching one. Ask only if the project is truly unclear; default priority `normal`.
2. Folder: `todos/open/<today>-<slug>/` — slug is kebab-case, ASCII, ≤ 6 words. On collision append `-2`.
3. Images:
   - User gave a file path → `cp` it into the folder as `img<N>.<ext>` (keep extension).
   - Pasted image with `[Image: source: <path>]` → `cp` that path to `img<N>.<ext>` (preferred; works reliably).
   - Pasted image without any path → run `<scripts>/clipboard-image.sh <folder>/img<N>.png` (macOS). If it fails, ask for the file path or to copy the image to the clipboard again.
   - Number images per todo: img1, img2, … (continue after the highest existing number). Embed each as `![imgN](imgN.png)` — no descriptive alt text.
4. URLs → for each, run `<scripts>/link-title.py <url>` (GitLab issues/work items/MRs via `glab`, GitHub issues/PRs via `gh`, otherwise og:title/`<title>`). Empty output → try WebFetch for a title; still nothing → use a short title derived from the URL. The fetched title is raw input only — rewrite it into a short, understandable title (≤ ~8 words, in the language of the todo, no site names/SEO noise like "| Medium" or "- Wikipedia"); keep a ref prefix like `website#179:` / `website!42:`. Add `- [Short title](url)` under `## Links`. Never paste page content. A URL that *is* the task (e.g. "read this article", an issue) also gives the todo its title.
5. Email or long text (more than a few lines, or clearly pasted mail/chat/spec) → save verbatim to `email<N>.md` (mail) or `text<N>.md` (other), numbered like images. Start the file with `# <Subject or short title>`, then for mail a `From / To / Date` block if present, then the content unchanged. Link it under `## Attachments` as `- [<Subject or short title>](email1.md)`. The todo body gets only a 1–2 sentence summary of what to do.
6. Write `todo.md`, run `<scripts>/save.sh "todo: add <slug>"`, reply in one line with the link to the new todo.

Several todos in one message → one folder each. Section names (`Links`, `Attachments`, `Notes`) may be in the todo's language; stay consistent with existing todos.

## Complete / update / list

- **Done:** set `done: <today>` in frontmatter, `mv todos/open/<dir> todos/done/`, `save.sh "todo: done <slug>"`.
- **Update:** edit `todo.md`; append dated lines under `## Notes` instead of rewriting history. New images, links and attachments follow the same rules and numbering. `save.sh "todo: update <slug>"`.
- **Reopen:** clear `done:`, move back to `todos/open/`, `save.sh "todo: reopen <slug>"`.
- **List / "what's up next":** run `save.sh`, read `TODO.md`, summarise; filter by project/priority/due on request. Then run `<scripts>/forge-status.py`: for every todo it prints (all linked issues/MRs/PRs closed/merged), offer to mark it done — never complete without a yes.
- **Today overview** ("/todo today", "what's urgent"): run `<scripts>/index.py --today` and `<scripts>/forge-status.py`; show overdue + due ≤ 7 days + high priority, plus the closed-issue hints. Short, no full list.
- **Delete:** only on explicit request, confirm first (removes images and attachments too), then `save.sh "todo: delete <slug>"`.

## Start work on a todo (zidev)

Only if [`zidev`](https://github.com/zinoodev85/zido#zidev) is on `PATH` (`command -v zidev`); otherwise tell the user how to start a Claude session on the todo by hand (the prompt from step 2) and stop.

"Start a session for the todo": the new session must know the todo from its first message.

1. Find the repo, fresh clone next to existing checkouts (`git clone --reference <old checkout> --dissociate`), new branch off the default branch. Never reuse a checkout that is on another branch. A linked worktree can't be a `--reference` (git refuses): then clone plainly. Run `zidev new` only after the clone succeeded (`&&`), else the session starts in a missing folder and burns its prompt.
2. `zidev new <dir> --prompt "<prompt>"` — the prompt is the session's first message, in the todo's language. A good prompt carries a goal, a finish check that can pass or fail, the proof to show, and the known facts:
   `<pstack> Work on the todo <abs path todo.md> (slug: <folder name>); read it first, with all images and attachments in its folder. Goal: <what is wrong or wanted, 1–2 sentences>. Done when: <check that can pass or fail>. Proof: <evidence to show>. Known: <facts only>. Checkout: <dir>, branch: <branch>. Don't change any code yet<, repro first>: restate the problem in your own words, make a short plan, explain it to me simply (open questions first) and wait for my go. Note progress under ## Notes in the todo; when the task is done (MR merged or similar), ask me and then close the todo with the todo skill (Done).`
   - `<pstack>`: `/pstack:poteto-mode` when the [pstack](https://github.com/cursor/plugins/tree/main/pstack) plugin is installed (`claude plugin list | grep -q pstack`) and it is code work; it picks its own playbook (bug fix, feature, investigation …). Otherwise leave it out.
   - **Goal:** the outcome, not the how. No implementation steps.
   - **Done when:** concrete and pass/fail, from the issue's acceptance criteria or the report (e.g. "the field shows again after DE → AT → DE", "spec for X green and MR open"). Never "make it better". Unclear → `Done when: propose a checkable finish`, and it becomes the first open question.
   - **Proof:** test output before/after, a screenshot of the flow, a stored value, a number before/after.
   - **Known:** repro steps, error text, links, MR, related files, who reported it. Facts only, never a guess at the cause: the agent searches wherever a theory points.
   - **repro first:** add it for bugs.
   - Never list skills or playbooks in the prompt.
   - Not code work (read, watch, decide, write a mail) → drop Done when/Proof if they make no sense.
   The slug is the folder name (`<date>-<slug>`), unique by construction.
3. `zidev rename-project <dir> "<short name>"`.
4. Assign: set `zidev: <dir>` in the frontmatter (TODO.md shows it as "▶ in progress"), append a dated line under `## Notes` (dir, branch, MR), `save.sh "todo: update <slug>"`.

## Now: add and start in one go

`/todo now <request>` (also "do it now", "start right away"): the whole process, no stop in between.

1. **Add** as above (images, links, attachments), `save.sh "todo: add <slug>"`.
2. **Start** as above: repo, fresh clone + branch, `zidev new … --prompt`, rename project, assign (`zidev:` + note), `save.sh "todo: update <slug>"`. The prompt is the one from Start: goal, finish check, proof, facts, a wait for the user's go; never "implement" in it.
3. Ask only when the repo is truly unclear (one question, with candidates found on GitLab/GitHub). No repo at all (not code work) → `zidev new` in the todo folder itself.
4. Reply: link to the todo, the zidev project name, dir + branch.

## Scripts (in `<scripts>`)

- `save.sh "<msg>"` — rebuild `TODO.md` + git commit (+ push if a remote exists). Run after **every** change.
- `index.py [--today]` — rebuild `TODO.md`, or print the daily overview. `TODO_LANG=de` for German labels, `TODO_TITLE` for the heading.
- `link-title.py <url>` — raw page / issue title.
- `forge-status.py` — open todos whose GitLab/GitHub links are all closed/merged.
- `clipboard-image.sh <out.png>` — save clipboard image (macOS).
