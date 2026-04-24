# claude-skills

A small set of Claude Code skills we use daily in the ELF Labs working environment — cleaned up for general use. They install into your local `~/.claude/skills/` directory and trigger automatically when you say the right things in conversation.

These skills work fully stand-alone. A couple of them are richer when paired with a self-hosted memory layer (see EverMemOS section below), but none **require** it — they all gracefully fall back to file-based memory or skip memory entirely.

**License:** Apache-2.0, same as the rest of this repository.

---

## The skills

| Skill | What it does | Starts a conversation first? |
|---|---|---|
| [`sync-pollinate`](./sync-pollinate/SKILL.md) | End-of-session: cross-pollinates findings across your projects and syncs state to memory. Self-configuring — asks about your memory setup on first run and rewrites itself to match. | ✅ |
| [`swarm-audit`](./swarm-audit/SKILL.md) | Parallel multi-agent audit for multi-file pipelines → root-cause synthesis → numbered fix plan with smoke gates. Use before any production cutover. | ❌ |
| [`research-synthesis`](./research-synthesis/SKILL.md) | Bi-directional cross-pollination when starting a new project — pulls relevant code/patterns/data from your existing projects into the new one, and pushes new discoveries back out. Requires a small project-inventory file you maintain. | ❌ |
| [`check-progress`](./check-progress/SKILL.md) | Multi-machine status dashboard — parallel health check across your hosts (SSH, Docker, GPU, queues, logs). Template skill; requires filling in your own host list before first use. | ❌ |

---

## Installing a skill

Each skill lives in a single `SKILL.md` file. To install:

1. Create a directory under `~/.claude/skills/` named after the skill — e.g. `~/.claude/skills/sync-pollinate/`
2. Copy the `SKILL.md` file into that directory
3. Done — Claude will auto-discover it on next session start

To uninstall, delete the directory.

---

## Optional: EverMemOS integration

A couple of these skills can use a richer semantic-memory layer than plain files. We run [EverMemOS](https://github.com/openMem-org/EverMemOS) — an open-source self-hosted memory system with persistent semantic search, timestamped entries, and cross-session recall.

If you want continuous memory across sessions (with search, tagging, and cross-project connections), `sync-pollinate` will offer to walk you through EverMemOS setup on first run. Takes about 20 minutes in Docker. Fully optional — vanilla file mode works great if you don't want another service running.

**Privacy model:** EverMemOS is fully self-hosted. Your data lives on your machine. Nothing leaves your hardware unless you explicitly configure it to (e.g., a peer mesh over Tailscale between your own devices). No central server, no hosted version, no telemetry.

---

## Philosophy

These skills share a few design choices:

- **Collaborative over configurational.** `sync-pollinate` asks questions instead of making you fill out a config form; `check-progress` and `research-synthesis` ship as templates you customize for your own environment
- **Parallel over serial.** `swarm-audit` and `check-progress` both depend on running things concurrently — serial defeats the point
- **Root causes over symptoms.** `swarm-audit`'s synthesis step is the load-bearing piece — a bug list without causes just makes implementers serial-debug again
- **Reuse over reinvention.** `research-synthesis` exists because every new project wants to rebuild things the parent org already has
- **No telemetry, no accounts, no hosted anything.** Everything runs locally. Your data is yours.

---

## Contributing

Open an issue or a PR on the repo. Small fixes, clarifications, or generalization improvements welcome. If you've written your own skill in this style, feel free to propose adding it.
