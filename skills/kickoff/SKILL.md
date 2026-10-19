---
name: kickoff
description: Research a task (GitLab/GitHub issue or MR, todo folder, or pasted text) and write the first prompt for a new Claude session that will do it — goal, a done check that can pass or fail, proof, facts, open questions. Read-only; it never starts the work. Use for "/kickoff <url|todo|text>", "prepare a prompt for this issue", "write a kickoff prompt", "Prompt für die Session vorbereiten", and from the todo skill before it starts a session.
---

# Kickoff

Turn a task into the best first message for the session that will do it. The session starts cold: everything it needs to aim right must be in the prompt or one click away, and nothing in it may steer it wrong. You research; you don't solve. Never edit code, comment on the issue, or start work.

`<scripts>` = the `scripts/` folder next to this file.

## 1. Gather

Input is an issue/MR/PR URL, a todo folder (`todo.md` + images + attachments), or pasted text. Collect all of it; keep the bulky reading out of your own context where you can.

- **Issue / MR / PR** (every URL found in the input or the todo): `<scripts>/issue-context.py <url> --images <dir>` prints title, state, labels, milestone, assignees, description, every comment, related MRs/issues and downloads attached images. `<dir>` = the todo folder when there is one, else a scratch dir. Look at every image (Read). Follow related MRs: an open MR that already works on this is the most important fact you can find (its branch, state, what it changed: `glab mr diff` / `gh pr diff`, summarised).
- **Todo folder:** `todo.md`, every image, every `email*.md` / `text*.md`.
- **Other links** (docs, chats, tickets you can't open): note them as links the session can follow; don't guess their content.
- **Code** (when a checkout exists): one Explore subagent, read-only, briefed with the task in 2–3 sentences, returns ≤ 10 entry points: files, components, specs, routes, flags that the task names or clearly touches, each with one line on what it is. Pointers only, not a diagnosis. Also note how to run the relevant tests (from package.json / Makefile / README).

## 2. Decide

- **Already done?** All linked issues closed and MRs merged, or the todo's notes say it's finished → stop. Don't write a work prompt; report "already done" with the evidence (MR, release, state) and what might be left (e.g. a release not yet rolled out), so the caller can offer to close it.
- **Kind:** bug, feature, refactor, investigation, perf, docs, or non-code (read, decide, reply, write).
- **Settled vs open:** where comments disagree or the issue changed its mind, the latest decision by the issue owner/PM wins; list the rest as open questions.
- **Scope:** what the issue says is in and out. Anything a commenter explicitly ruled out becomes a constraint.

## 3. Write the prompt

In the language of the task, slot labels too (`Ziel`, `Fertig, wenn` … or `Goal`, `Done when` …; never both). Short sentences, ≤ ~250 words before the closing block; link instead of paste.

```
<prefix> <task line>
Goal: <the outcome, 1–2 sentences — what is wrong or what should exist, never how to build it>
Done when: <checks that can pass or fail>
Proof: <the evidence to show>
Known:
- <fact> (<source>)
Open questions:
- <question>
Constraints: <scope limits, ruled-out approaches, target branch/milestone>
<closing>
```

- **prefix:** `/pstack:poteto-mode` when the pstack plugin is installed (`claude plugin list 2>/dev/null | grep -q pstack`) and the kind is code work; it picks its own playbook from the goal and done check. Otherwise nothing.
- **task line:** what to read first — the todo path (with "read it first, with all images and attachments in its folder") and/or the issue URL; checkout dir and branch when known.
- **Done when:** from the acceptance criteria, the reporter's expectation, or the repro inverted ("after AT → DE → AT the field is visible again"). Add the real test/lint command when there is one — in a monorepo the one for the affected package, with its directory (the root script often runs another app). Never "works", "better", "clean". If no honest check exists, write `propose a done check that can pass or fail` and make it the first open question.
- **Proof** by kind: bug → repro before, the same steps after, plus the failing-then-green spec; UI → screenshots before/after of the named flow; API → request and response; perf → numbers before/after with run count; investigation → an answer with file:line sources; non-code → the draft/decision itself.
- **Known:** facts with their source in brackets: repro steps, exact error text, environment/browser/tenant, who reported it, the existing MR and its state, entry points from the code scan, test command. **No guess at the cause**, not even phrased softly ("probably", "vermutlich", "seems like the …") — the session searches wherever a theory points. A theory written by a human in the issue is a fact about the issue: quote it as "<name> suspects …". A cause confirmed by a merged fix or a maintainer's diagnosis is a fact: one line with its source (MR, comment).
- **Open questions:** only ones that change what gets built; who can answer, if known.
- **Constraints:** add `repro first` for bugs. Add what comments ruled out. No skill or playbook lists.
- **closing:** the caller supplies it (e.g. the todo skill's "don't change code yet, plan, wait for my go, note progress, close the todo"). Without a caller: `Don't change any code yet: restate the problem in your own words, make a short plan, open questions first, and wait for my go.`

## 4. Check before handing it over

Reread the prompt as the cold session would and fix it until all hold:

- Every slot has content or an explicit open question; no `<placeholder>` left.
- Each done check can visibly fail.
- No cause guesses, no implementation steps, no skill lists.
- Every fact has a source; every image/attachment the session needs is in the todo folder or linked.
- An open MR/branch for this task is named, so the session continues it instead of starting over. A merged one is named as history; new work starts on a new branch off the default branch.
- Every constraint comes from a source (issue, comment, todo, caller); none invented.

## 5. Output

- With a todo folder: write the prompt to `<todo folder>/kickoff.md` (`# Kickoff` + the prompt) and link it under the todo's attachments section. The caller passes the file's content as the session prompt.
- Standalone: print the prompt in a code block, then one line each for what you could not open and the open questions.
