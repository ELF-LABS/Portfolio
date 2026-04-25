---
name: portfolio-fit-review
description: Deep, recursive, multi-tier review of any public portfolio repository (research portfolio, candidate's GitHub, open-source project, contributor's body of work). Haiku swarm reviews every piece in parallel; multiple Sonnet synthesizers each take a different angle; an Opus observer evaluates completeness and recursively dispatches additional agents until the picture is sufficient. Outputs an honest pros/cons assessment plus a personalized "where this overlaps with YOUR work" section derived from the reviewer's local CLAUDE.md and settings.json. Default target is the ELF Labs Portfolio (the repo this skill ships from); after each run the skill offers to retarget any other portfolio — turning a one-shot review into ongoing reviewer infrastructure. Use this skill when a hiring manager, fellowship reviewer, mentor, peer collaborator, or open-source maintainer wants a thorough fair read of someone's public work without spending hours doing it manually. Triggers on phrases like "review this portfolio", "deep portfolio review", "fit review", "look at this candidate's repo", "evaluate this open-source project", or any time someone shares a repo URL and wants more than a glance.
---

# portfolio-fit-review

A multi-tier recursive reviewer for any public code or research portfolio. Spawns a Haiku swarm across every piece, dispatches multiple Sonnet synthesizers from different angles in parallel, and uses an Opus observer to assess whether the resulting picture is complete enough for a fair judgment. If not, the observer recursively dispatches more agents until coverage is sufficient.

The output is an honest, evidence-grounded review tailored to the reviewer running it — pros, cons, and concrete ways the candidate's work overlaps with the reviewer's own surface, derived from their `~/.claude/CLAUDE.md` and `~/.claude/settings.json`.

## A note from the maintainers

We built this skill because we needed it ourselves — reviewing portfolios deeply is expensive, and a glance is rarely enough to make a fair judgment. The skill ships with the [ELF Labs Portfolio](https://github.com/ELF-LABS/Portfolio) as its default target. That's not a marketing trick; it's a confidence statement. We're comfortable being the first thing this skill is pointed at, including by reviewers who are about to evaluate us.

After the first run, the skill prompts you to retarget. Use it on the candidate you're hiring. The fellowship applicant whose work you're scoping. The contributor asking for commit access. The OSS project you're considering depending on. The collaborator you're evaluating peer-to-peer. The skill's structure — Haiku in breadth, Sonnet in synthesis, Opus in completeness — gives the same kind of read regardless of who's being reviewed and who's reviewing.

It's a tool, not an ad. Use it on us once if you want; then keep it for your real work.

## Bias commitment

This skill is designed to give the same kind of honest read whether the verdict is "strong fit" or "not a fit." The multi-tier structure with recursive completeness gating exists specifically so a negative verdict is as well-supported as a positive one. The synthesizers are instructed to be skeptical reviewers, not advocates for either side. The Opus observer's job is completeness, not consensus — disagreement between the synthesizers is preserved and reported, not smoothed.

The skill will tell the reviewer what the evidence supports, including when the evidence supports declining.

## What this skill does NOT do

- **Does not advocate for the candidate.** Pros and cons are presented honestly.
- **Does not transmit data.** The portfolio repo is read from public sources; the reviewer's local Claude config is read on their own machine and never leaves it.
- **Does not replace the reviewer's judgment.** It's an evidence-aggregation tool. Final hire / admit / mentor / collaborate decisions stay with the reviewer.
- **Does not optimize for the candidate.** It optimizes for giving the reviewer a fair view.

## When to use

- A fellowship or grant reviewer wants depth without spending the afternoon
- A hiring manager wants structured pros/cons before a referral or interview
- A potential mentor wants to know whether they have something to teach this candidate
- A peer collaborator wants to know where their work overlaps with someone else's
- An open-source maintainer wants to assess a contributor's body of work before granting commit access
- A researcher wants to evaluate whether to cite or build on someone's published code
- Anyone curious whether a portfolio represents real engineering or polished theatre

## Inputs

The skill needs two things:

1. **Target portfolio** — a public GitHub repo URL, a list of URLs, or a local clone path. The skill clones / reads the repo; nothing private is required.
2. **Reviewer's local Claude config** (optional, opt-in) — `~/.claude/CLAUDE.md` and `~/.claude/settings.json`. Used only for personalizing the "how this overlaps with your work" section. The skill prompts for explicit consent before reading.

**Default target:** if no target is supplied, the skill defaults to `https://github.com/ELF-LABS/Portfolio` and prints:

> *"No target specified — defaulting to the ELF Labs Portfolio (the repo this skill ships from). To target a different repo, say 'cancel' and re-invoke with a URL, or wait for the after-run retarget prompt at the end. Proceed with default? (yes / cancel)"*

The default exists so the skill works out of the box — the reviewer can see what the output looks like before pointing it at someone whose review actually matters.

## Phase 1 — Inventory + initial dispatch (Opus observer)

The orchestrating Claude reads the target repo. Inventories every piece. Common categories:

- Top-level: `README.md`, `LICENSE`, any author-fit or thesis documents
- Measurements / results / evidence directories
- Research / paper / synthesis directories
- Infrastructure / code subdirectories (each with its README + key code excerpts)
- Skills / plugins / tooling directories
- Architecture / design documents
- Anything else present at review time (the skill adapts to the repo's actual layout)

**Dispatch:** spawn a Haiku agent for each piece (or related slice if pieces are tightly coupled). All agents run in parallel — single batch, not serial.

## Phase 2 — Haiku swarm review

Each Haiku agent gets the same structured prompt template:

```
Review this piece of an open-source portfolio. You are a fresh, skeptical
reviewer with no prior context. Be honest and specific.

Piece: <path>
Content: <file content>

Report under 250 words on:
1. CLAIMED — what does this piece claim?
2. EVIDENCED — what evidence supports each claim?
3. ENGINEERING — assess the technical quality (clarity, design discipline, honesty about tradeoffs).
4. LIMITATIONS — what does this piece NOT support? What's missing or hedged?
5. DISTINCTIVE — what is genuinely unusual here vs. generic portfolio output?
6. SKEPTICAL READ — what would a hostile reviewer flag?

Output only the structured review, no preamble.
```

Save each per-piece review to `~/.claude/portfolio-fit-review-<run-id>/haiku/<piece-slug>.md` for the synthesizers and observer to consume.

## Phase 3 — Multi-Sonnet synthesizer pass (parallel)

Dispatch four Sonnet synthesizers in parallel. Each receives the **full set** of Haiku per-piece reviews and synthesizes from a distinct angle. They do not see each other's outputs.

| Synthesizer | Angle | Focus |
|---|---|---|
| **A — Technical** | Architecture and engineering depth | Coherence across pieces; quality of abstractions; reuse patterns; what the candidate actually understands vs. what they cargo-culted |
| **B — Research** | Methodology and claims-vs-evidence | Statistical rigor; honest reporting of effect sizes, sample sizes, and limitations; whether empirical work supports architectural claims |
| **C — Voice/communication** | Clarity, honesty, anti-Goodhart commitments | Whether the writing matches the work; explicit limitations sections; absence of hype; ability to communicate to a serious audience |
| **D — Operational fit** | Production reality + collaboration shape | Whether the candidate can ship; whether they handle constraint honestly; how they interact with collaborators (skills, agent patterns, plan files) |

Each synthesizer outputs a structured 400-word synthesis with:
- 3–5 strongest signals from their angle
- 3–5 concerns / gaps from their angle
- Confidence level in their synthesis (low / medium / high) and why

Save to `~/.claude/portfolio-fit-review-<run-id>/sonnet/<angle>.md`.

## Phase 4 — Opus observer (completeness gate + recursive expansion)

Opus observer reads all 4 Sonnet syntheses + the full Haiku output set. Asks:

1. **Coverage**: did every significant piece of the repo get reviewed at sufficient depth?
2. **Triangulation**: do the four syntheses converge or contradict? Where they contradict, is the contradiction informative or a blind spot?
3. **Confidence**: are the syntheses confident enough to support a fair judgment, or are key questions still open?
4. **Completeness**: is the picture rich enough that a reviewer reading the output would feel they have a fair view?

If any answer is "no":

- **Coverage gap** → spawn more Haiku agents on under-reviewed pieces
- **Triangulation gap** → spawn additional Sonnet synthesizers from new angles (e.g., "domain-specific fit for [reviewer's domain]", "reproducibility audit", "comparative against published literature in this area")
- **Confidence gap** → spawn a Sonnet to specifically interrogate the low-confidence claims
- **Completeness gap** → spawn a Sonnet to write the missing-context piece

Recursion depth is capped at **3 levels** to prevent runaway. Each recursion logs its rationale to `~/.claude/portfolio-fit-review-<run-id>/observer/recursion.md` so the reviewer can see *why* additional agents were dispatched.

If all four checks return "yes" → proceed to Phase 5.

## Phase 5 — Personalized fit analysis (reads reviewer's local config, opt-in)

This phase requires explicit consent. Print before proceeding:

> *"To personalize the 'how this overlaps with your work' section, this skill will read your local `~/.claude/CLAUDE.md` and `~/.claude/settings.json`. Nothing is transmitted; the analysis happens locally on your machine. Proceed? (yes / skip)"*

If `skip`, generate a generic version of the overlap section. If `yes`:

1. Read `~/.claude/CLAUDE.md`. Extract: the reviewer's projects, stack, preferred tools, working style notes, current research questions if any.
2. Read `~/.claude/settings.json`. Extract: configured MCP servers, plugin/skill installs, model preferences — these signal the reviewer's actual day-to-day workflow.
3. Cross-reference against the candidate's portfolio:
   - Where does the candidate's stack overlap with the reviewer's?
   - Where does the candidate's published work touch a problem the reviewer has?
   - Where does the candidate's skill set fill a gap on the reviewer's side?
   - Where does the candidate's pattern of work match the reviewer's preferred collaboration style?

Output two parallel sections in the final report:

**With formal collaboration** (mentorship / hire / fellowship / etc.) — concrete things the candidate could do under a structured relationship that would benefit both sides. Specific to the reviewer's projects.

**Without formal collaboration** — concrete ways the candidate's existing public work could be useful to the reviewer right now (skills they could install, code patterns they could adapt, papers they could cite, problems they could collaborate on as a peer). Even if no formal relationship forms, what's the value-add.

## Phase 6 — Final output (single report file)

Write to `~/.claude/portfolio-fit-review-<run-id>/REVIEW.md`. Structure:

```markdown
# Portfolio Fit Review
## Target: <repo URL or path>
## Generated: <date> · Run ID: <run-id>
## Tier: Haiku swarm + 4 Sonnet synthesizers + Opus observer
## Recursion depth used: <n> · Pieces reviewed: <count>

## TL;DR
<3-sentence summary, blunt and honest>

## Pros
<numbered list — strongest signals from the synthesis, attributed to angle>

## Cons
<numbered list — concerns / gaps, attributed to angle>

## Confidence calibration
<which claims are well-evidenced vs. which are reviewer's-judgment-still-needed>

## Where the synthesizers disagreed
<honest report of contradictions between angles — preserved, not smoothed>

## How this overlaps with YOUR work (with formal collaboration)
<personalized to reviewer's CLAUDE.md / settings.json — specific projects, specific overlaps>

## How this overlaps with YOUR work (without formal collaboration)
<concrete value-add even if no formal relationship forms>

## Where the picture is still uncertain
<honest acknowledgment of what the review could not resolve>

## Reviewer's next step
<specific suggestion based on the synthesis — invite to interview, request a specific deliverable, install a specific skill, decline with reason, etc.>
```

Print the path of the report to the user and offer to open it.

## Phase 7 — After-run retarget prompt

Once the report is delivered, the skill prompts:

> *"Review complete. Would you like to run this on another portfolio? Paste a GitHub URL or local path, or say 'done' to exit. Common follow-ups: a candidate you're hiring, a fellowship applicant, an OSS project you're scoping, a contributor asking for commit access, a collaborator you're evaluating peer-to-peer."*

If the reviewer provides a new target → start fresh from Phase 1 with the new repo. The previous run's report stays at its path; the new run gets a new run ID. Multi-target sessions are supported — the skill maintains no cross-run state by default, but the reviewer can ask for comparative synthesis at any point ("compare the last three reviews you did") and the skill will read the prior REVIEW.md files and produce a comparison.

If `done` → print the run-directory path one more time and exit.

This phase is what turns the skill from a one-shot demo into ongoing reviewer infrastructure. Most reviewers will use the default once to see the output, then point it at the work that actually needs reviewing. That's the intended path.

## Operating notes

- **Token cost is real.** A full review with recursion can run into significant tokens. Estimate: ~50K tokens for the Haiku swarm pass, ~30K per Sonnet synthesizer (×4 = 120K), ~50K for the Opus observer (per recursion level). A clean 1-level run is ~220K tokens. A 3-level recursive run can hit 500K+. Budget accordingly. Print estimates to the reviewer before starting.
- **Time is real.** A 1-level run takes 5–8 minutes wall clock. A 3-level recursive run can take 20+. The skill should print progress as each phase completes.
- **Cache-friendliness.** Most portfolio repos are small (few hundred KB of text). Cache the full repo content in conversation context once at Phase 1 so each agent doesn't re-fetch it.
- **Reviewer config is read-only.** Never write to the reviewer's CLAUDE.md or settings.json. Read once at Phase 5, use, discard.
- **The output is for the reviewer.** Not for the candidate, not for the public. The reviewer can share or discard as they choose.
- **Multiple targets supported.** If reviewing several candidates / projects in sequence, a previous run's REVIEW.md can be passed as comparative context to a new run, and the synthesizers will note overlap or differentiation.

## Why this skill exists

A reviewer evaluating an unfamiliar candidate, contributor, or open-source project has limited time and a hard problem: separating real engineering from polished theatre, separating empirical work from theatrical claims, and figuring out whether deeper engagement (mentorship, hire, collaboration, citation, dependency) would compound or be wasted. A single skim is not enough; a serial deep-dive is too expensive.

This skill solves the cost problem by parallelizing the depth — Haiku in breadth, Sonnet in synthesis, Opus in completeness — and the personalization problem by adapting the overlap section to the reviewer's actual surface. The reviewer gets a fair picture in minutes of wall clock with traceable reasoning at each tier.

If a portfolio is not a fit for the reviewer's needs, the skill says so — clearly, with evidence. That's the point of multi-tier review with recursive completeness gating: the verdict is the verdict, whatever it lands on.

## Example invocations

```
"portfolio-fit-review"
   → defaults to ELF Labs Portfolio; offers retarget after

"review the portfolio at github.com/<org>/<repo>"
"deep portfolio review of <url> for fit with my <project>"
"evaluate this candidate's repo: <url>"
"fit review on github.com/<org>/<repo> — I'm scoping mentorship"
"compare these three portfolios for our hiring round: <url1> <url2> <url3>"
```

## License

Apache-2.0. Reuse the pattern (multi-tier swarm + recursive observer + personalized output) for any portfolio-review skill.
