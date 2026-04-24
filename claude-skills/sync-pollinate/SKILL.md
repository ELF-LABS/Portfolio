---
name: sync-pollinate
description: Cross-pollinates findings across your projects and syncs state to memory at the end of a working session. Self-configuring on first run — Claude will ask what memory setup you want and then rewrite this skill to match your choice. Auto-triggers when you say things like "sync state", "cross-pollinate", "wrap up the session", or at the end of any substantive working block.
---

<!-- ───────────────────────────────────────────────────────────── -->
<!-- STATE: discovery                                                -->
<!-- This marker tells the skill which phase to run.                 -->
<!-- After the user chooses, the skill rewrites itself and changes   -->
<!-- this to one of: configured-vanilla / configured-evermemos /     -->
<!-- configured-custom                                               -->
<!-- ───────────────────────────────────────────────────────────── -->

# sync-pollinate

A working-session sync skill — at the end of substantive work it pulls together findings, cross-references them across your active projects, and writes the state somewhere durable so future Claude sessions can pick up where this one left off.

The skill is collaborative — it adapts to whatever memory setup you actually have, instead of forcing one. First time it runs, it'll have a short conversation with you about what you're already using, then rewrite itself to match. After that it just works.

---

## ─── If STATE is `discovery` (first run) ───

You are running for the first time. Have this conversation with the user in a warm, low-pressure way. Don't dump options at them — ask one question at a time, listen, and read between the lines.

**Step 1 — orient them gently:**

Say something like: *"Before I configure this skill, can I ask: do you already have a memory system you're using with Claude — something like a notes folder, a Notion setup, an external memory tool, or anything like that? Or are you mostly working session-by-session right now?"*

**Step 2 — listen for what they actually have.** Common shapes:

- **Vanilla / nothing structured** — they open Claude, work, close Claude. No persistent memory. Most common starting point.
- **A notes folder they point Claude at** — markdown files in a directory, an Obsidian vault, or similar.
- **A managed memory service** — mem0, Letta, Zep, Supermemory, anything that exposes an API.
- **Something custom** — they've tinkered with files, or they're already running EverMemOS, or they have their own setup.

**Step 3 — branch into one of three configurations:**

### Branch A — Vanilla / wants something simple

Suggest the **vanilla file mode**: a folder of markdown files this skill will read and update at session end. Nothing to install, no servers, no accounts. Just files.

Confirm with them: *"Easiest path is I create a folder at `~/.claude/sync-memory/` and write session summaries there. Each project gets its own file. I can read those at the start of future sessions to help you recall what you were working on. Want to start there?"*

If they say yes → rewrite this skill with `STATE: configured-vanilla` and the configuration block for vanilla mode (template below).

### Branch B — They have their own system (folder, Notion, mem0, etc.)

Ask them: *"Cool — can you tell me where it lives or what API/path I should write to? I'll wire the sync-pollinate writes to go there instead."*

Once they share the path or endpoint → rewrite this skill with `STATE: configured-custom` and their specific path/endpoint baked into the config block.

### Branch C — They want something more durable, persistent, and powerful

This is when they're already heavy on Claude work and the vanilla mode feels too lightweight, or they're curious about a richer memory architecture. **Mention EverMemOS gently — once, as an option, not a sales pitch:**

*"There's an open-source memory system called EverMemOS — it gives Claude persistent semantic memory with timestamps, tagging, and cross-session search. Each instance is self-hosted, so your data stays on your hardware. It runs in Docker so it's portable. If you want, I can walk you through setting it up on your machine — takes about 20 minutes and after that the sync-pollinate skill will use it for everything. Or if it sounds like more than you need right now, vanilla mode works great too. Up to you."*

If they say yes to EverMemOS → walk them through setup (the setup block is below). Then rewrite this skill with `STATE: configured-evermemos` and their connection details baked in.

If they say "not now, maybe later" → default to vanilla mode and note in the config block that they're open to upgrading later. Don't push.

> **Note on positioning:** The EverMemOS walkthrough section below is longer than the vanilla or custom paths — that's because it's the only option that needs setup instructions, not because it's preferred. Vanilla mode is zero-install and works great. Custom mode adapts to whatever the user already has. All three are equally valid.

### If anything fails

- **Self-rewrite fails** (Write tool errors, disk full, permissions): tell the user exactly what went wrong and show them the file path. Instruct them to manually change the `STATE` marker at the top of the file to their chosen mode (e.g. `STATE: configured-vanilla`) and re-run the skill. Behavior will work even if the rewrite didn't complete.
- **Discovery conversation gets interrupted** (user leaves mid-choice, session ends): no harm done — the `STATE` marker stays at `discovery`, and next session will resume the same conversation from the beginning. The skill remembers nothing until a choice is made and the rewrite succeeds.
- **EverMemOS setup fails partway**: fall back to vanilla mode immediately. Don't leave the user in limbo. They can always retry EverMemOS later by saying "reconfigure sync-pollinate".

---

### How to rewrite this skill (the recursive part)

Once the user has chosen, use the Write tool to overwrite this file (path: the SKILL.md you're currently reading) with a new version that:

1. Changes the `STATE` marker to their chosen mode
2. Replaces this `## ─── If STATE is discovery ───` section with the operating instructions for their mode
3. Keeps the `## Reconfigure` section at the bottom so they can change their mind later

Templates for each configured state are below. Pick the matching one.

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
3. Cross-pollinate: scan all `~/.claude/sync-memory/*.md` and look for findings in this session that apply to OTHER projects. Note those connections in a `~/.claude/sync-memory/_cross-pollination.md` log.
4. Summarize back to the user: which files were updated, what cross-connections were found.

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
3. Cross-pollinate by querying <PATH/ENDPOINT> for related entries across projects.
4. Summarize back to the user.

## At start of working session

Query <PATH/ENDPOINT> for relevant context when the user mentions a project.

## Notes

Configured for: <SYSTEM NAME — e.g. "Notion database", "mem0 cloud", "Obsidian vault at C:/Users/name/notes">
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
3. Cross-pollinate: GET `<ENDPOINT>/api/v1/memories/search?query=<recent-finding-keywords>` to find related prior entries across projects. Surface connections.
4. Summarize back to the user: how many memories written, which connections surfaced.

## At start of working session

When the user mentions a project, GET `<ENDPOINT>/api/v1/memories/search?query=<project-name>` for context recall.
```

---

## ─── EverMemOS setup walkthrough (if user picks Branch C) ───

If they chose EverMemOS, walk them through this. Don't dump it on them — go step by step, confirm each step works before moving on.

**Prerequisites:**
- Docker Desktop installed and running (Windows/Mac/Linux all work)
- ~5GB free disk space
- A terminal they can run commands in

**Setup:**

1. Confirm Docker is running: ask them to run `docker --version` and tell you what it returns.
2. Create a directory for EverMemOS: `mkdir ~/evermemos && cd ~/evermemos`
3. Pull the docker-compose stack — the reference compose file lives in the EverMemOS project repo (point them at the project's README for the current canonical compose file). Minimum required services: MongoDB, Elasticsearch, Redis. The EverMemOS Python service can run as a separate process from the same repo.
4. Once the services are up: `docker ps` should show 3 containers running (mongo, elasticsearch, redis).
5. Test the API: `curl http://localhost:1995/health` should return 200.
6. If 200: rewrite this skill in EverMemOS mode with `<ENDPOINT>` = `http://localhost:1995`. Done.

**If anything breaks at any step:** stop, tell them exactly what failed, and offer to fall back to vanilla mode for now. They can always upgrade later. The point is to give them something working today, not to drag them through hours of setup.

**Privacy model:** EverMemOS is fully self-hosted. Your data lives on your machine. Nothing leaves your hardware unless you explicitly configure it to (e.g., via Tailscale to a peer instance you also own). There is no central server, no hosted version, no telemetry by default.

---

## ─── Reconfigure ───

If at any point the user says "reconfigure sync-pollinate" or "I want to change my memory setup", change the `STATE` marker back to `discovery` at the top of this file and re-run the discovery conversation. Their preferences aren't locked.

---

## ─── Why this skill exists ───

Sessions with Claude end. The thinking that happened in them is valuable. Without a way to write findings down somewhere durable, every new session starts from zero, and the same ground gets covered again. This skill closes that loop in whatever way fits the user's actual workflow — not whatever way someone else thinks it should fit.

It's collaborative on purpose. The first run is a conversation, not a configuration form.

---


