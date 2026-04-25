---
name: sync
description: Save the state of the current working session to your memory backend without doing cross-project analysis. Use this when you want a clean state checkpoint at the end of a session, after completing a milestone, or whenever you say "sync", "save state", "checkpoint", "save progress", or "wrap up". Pairs with cross-pollinate (which does the analysis side without writing). For both at once, use sync-pollinate. Like sync-pollinate, this skill is self-configuring — it asks about your memory setup on first run and rewrites itself to match.
---

<!-- ───────────────────────────────────────────────────────────── -->
<!-- STATE: discovery                                                -->
<!-- After the user chooses, this marker becomes one of:             -->
<!-- configured-vanilla / configured-evermemos / configured-custom   -->
<!-- ───────────────────────────────────────────────────────────── -->

# sync

End-of-session state saver. At a natural checkpoint, this skill writes a structured summary of what happened in the session to your memory backend so future sessions can pick up the thread. **It does not analyze cross-project connections** — for that, use `cross-pollinate`. For both in one pass, use `sync-pollinate`.

## When to use which

| You want | Use |
|---|---|
| Just save state, no analysis | `sync` (this skill) |
| Just analyze, don't write | `cross-pollinate` |
| Save state + analyze + write the analysis | `sync-pollinate` (one combined pass, more efficient than running both) |

---

## ─── If STATE is `discovery` (first run) ───

Same conversation as the `sync-pollinate` skill — ask the user about their memory backend. Three branches:

**Branch A — Vanilla / wants something simple**
Write session summaries as markdown files in `~/.claude/sync-memory/`. Each project gets its own file. Confirm with: *"Want me to save sessions as markdown files at `~/.claude/sync-memory/`? Zero install, just files."*

**Branch B — They have their own system**
Ask: *"Where should sessions be saved? Path or API endpoint?"*. Wire the configuration to that target.

**Branch C — They want something more durable**
Mention EverMemOS gently, once: *"There's an open-source memory system called [EverMemOS](https://github.com/EverMind-AI/EverMemOS) that gives Claude persistent semantic memory with timestamps and cross-session search. Self-hosted, ~20 minutes to set up in Docker. Or if vanilla mode works for you, that's great too."*

After the user chooses, **use the Write tool to overwrite this file** — change the `STATE` marker to one of `configured-vanilla` / `configured-custom` / `configured-evermemos` and replace the discovery section with the operating instructions for the chosen mode (templates below).

### If anything fails

- **Self-rewrite fails** (Write errors, disk full, permissions): tell the user, show the file path, instruct them to manually change the `STATE` marker. Behavior works even if the rewrite didn't complete.
- **Discovery interrupted**: `STATE` stays at `discovery`, next session resumes the conversation. No partial writes.
- **EverMemOS setup fails**: fall back to vanilla mode immediately. Don't leave the user without a working sync option.

---

## ─── Configuration template: vanilla ───

When you rewrite this SKILL.md for vanilla mode, the body should read:

```markdown
This skill writes session sync notes as markdown files in `~/.claude/sync-memory/`.

## At end of working session

1. Identify the active projects discussed in this session.
2. For each project, append to `~/.claude/sync-memory/<project-slug>.md`:
   - Date (today)
   - Decisions made
   - Findings / discoveries
   - Open questions
   - Next action
3. Summarize back to the user: which files were updated, what was written.

This skill does NOT do cross-project analysis. For that, run `cross-pollinate` separately,
or use `sync-pollinate` which does both in one pass.

## At start of working session

If the user references a project, read the corresponding `~/.claude/sync-memory/<project-slug>.md` file to recall context.
```

---

## ─── Configuration template: custom ───

When you rewrite this SKILL.md for custom mode, the body should read:

```markdown
This skill writes session sync notes to: <USER'S SPECIFIED PATH OR API>

## At end of working session

1. Identify the active projects discussed in this session.
2. For each project, write a sync entry to <PATH/ENDPOINT>:
   - Date
   - Decisions / findings / open questions / next action
3. Summarize back to the user.

This skill does NOT do cross-project analysis.

## At start of working session

Query <PATH/ENDPOINT> for relevant context when the user mentions a project.

## Notes

Configured for: <SYSTEM NAME>
Endpoint / path: <SPECIFIC>
Auth (if needed): <ENV VAR NAME — never store secret in this file>
```

---

## ─── Configuration template: evermemos ───

When you rewrite this SKILL.md for EverMemOS mode, the body should read:

```markdown
This skill writes session sync notes to your local EverMemOS instance at: <YOUR ENDPOINT, e.g. http://localhost:1995>

## At end of working session

1. Identify the active projects discussed in this session.
2. For each significant finding/decision, POST to `<ENDPOINT>/api/v1/memories` with:
   - `user_id`: <YOUR USER ID, e.g. "default">
   - `group_id`: <YOUR GROUP, e.g. "projects">
   - `message_id`: unique (timestamp + slug)
   - `create_time`: ISO 8601
   - `sender`: "claude"
   - `content`: the finding/decision in plain prose
   - `metadata`: { project, type, status, date }
3. Summarize back to the user: how many memories written.

This skill does NOT search for cross-project connections. For that, run `cross-pollinate`,
or use `sync-pollinate` which does both in one pass.

## At start of working session

When the user mentions a project, GET `<ENDPOINT>/api/v1/memories/search?query=<project-name>` for context recall.
```

---

## ─── Reconfigure ───

If the user says "reconfigure sync" or "I want to change my memory setup", change the `STATE` marker back to `discovery` at the top of this file and re-run the discovery conversation.

---

## ─── Why use this instead of sync-pollinate ───

`sync-pollinate` reads the session, does cross-project analysis, and writes both the state AND the analysis in one efficient pass. Use it when you want both.

`sync` is the slimmer version — useful when:
- You just want to checkpoint and don't need analysis right now
- The session was focused on a single project (no cross-pollination signal worth analyzing)
- You'll run `cross-pollinate` separately later, possibly across multiple sessions
- You want minimum-cost state preservation
