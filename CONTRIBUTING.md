# Contributing

This repo is the public portfolio for ELF Labs — research, measurements, and infrastructure excerpts. Most work happens in private staging; this repo is the curated surface.

## Branching

- `main` is the shipped state.
- Work branches follow `<type>/<short-slug>`:
  - `feat/...` — new content or capability
  - `fix/...` — corrections to existing content
  - `chore/...` — repo hygiene, CI, docs
  - `docs/...` — narrative/README/measurements prose changes

## Commits

- Conventional Commits style: `type(scope): subject`
- Keep subjects under ~72 chars.
- Prefer small, reviewable commits over large sweeps.

Examples:
- `fix(readme): correct p-value in pipeline A result`
- `chore(git): add baseline repository hygiene files`
- `docs(measurements): clarify held-out split methodology`

## Pull requests

Before opening a PR:

1. Local syntax check on any Python touched: `python -m py_compile <file>`
2. Line endings + final-newline via `.editorconfig` / `.gitattributes` (your editor should handle it).
3. No secrets, keys, or `.env` files staged.

PR body should include:

- **What changed** — concise bullet list.
- **Why** — what problem / reviewer concern it addresses.
- **Verification** — commands run + results.

## Scope

Keep PRs small and merge-safe. Do **not** change:

- Experiment claims or metric numbers without a matching measurement-file update.
- Model/training logic excerpts in `infrastructure/` (these mirror production and are audited separately).
- License or attribution headers.

## Licensing

By contributing, you agree your contributions are licensed under the repository's [Apache License 2.0](LICENSE).
