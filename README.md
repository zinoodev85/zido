# claude-todo

A `/todo` skill for [Claude Code](https://claude.com/claude-code): tell Claude what needs doing, paste a screenshot, a link or a mail, and it files a todo in a plain git repo of Markdown folders.

```
/todo fix the checkout bug https://gitlab.com/acme/shop/-/issues/179
/todo                        (with a pasted screenshot)
/todo what's up next
/todo today
/todo done checkout bug
```

## Install

```sh
brew install zinoodev85/tap/claude-todo
claude-todo install      # links the skill to ~/.claude/skills/todo
claude-todo init         # creates the todo repo at ~/todos
```

`brew upgrade claude-todo` updates the skill in place. Without Homebrew: clone this repo and run `bin/claude-todo install`.

## How todos are stored

```
~/todos/                       # $TODO_HOME, a git repo (add a remote to sync)
  todos/open/2026-10-06-fix-checkout-bug/
    todo.md                    # frontmatter (title, project, priority, due, …) + text
    img1.png                   # pasted screenshots
    email1.md                  # pasted mails / long texts, verbatim
  todos/done/…                 # completed todos move here
  TODO.md                      # generated index: due soon, then by project
```

Every change is committed (and pushed, if the repo has a remote).

## Features

- **Images**: pasted screenshots and file paths are copied into the todo folder.
- **Links**: titles are fetched; GitLab issues/MRs (`glab`) and GitHub issues/PRs (`gh`) work on any host you are logged in to, private repos included.
- **Mails and long texts** are saved verbatim as attachments; the todo gets a short summary.
- **Closed-issue check**: `/todo what's up next` lists todos whose linked issues/MRs/PRs are all closed or merged and offers to mark them done.
- **`/todo now …`**: add a todo and start a Claude session on it right away (needs `zidev`, see below).

## Settings

| Variable | Default | |
|---|---|---|
| `TODO_HOME` | `~/todos` | where the todo repo lives |
| `TODO_LANG` | `en` | labels in `TODO.md` (`en`, `de`) |
| `TODO_TITLE` | `TODOs` | heading of `TODO.md` |

Set them for Claude Code in `~/.claude/settings.json`:

```json
{ "env": { "TODO_HOME": "/Users/me/work-todos", "TODO_LANG": "de" } }
```

## zidev

The "start a session" steps (`/todo now`, "start work on this todo") use `zidev`, a tmux-based manager for parallel Claude Code sessions: it clones the repo, opens a session with the todo as its first message and marks the todo as in progress. `zidev` is not published yet; without it the skill gives you the prompt to start a session by hand.

## Requirements

`python3`, `git`. Optional: `glab` / `gh` for issue titles, macOS for clipboard images.

## License

MIT
