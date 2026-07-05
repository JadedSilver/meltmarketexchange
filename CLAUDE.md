# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## Current state of the repository

**This repository is a fresh scaffold. As of this writing it contains no application code.**

The entire tracked contents are:

- `README.md` — a single-line title (`# meltmarketexchange`)
- `CLAUDE.md` — this file

There is no build system, no dependency manifest (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.), no source directory, no tests, and no CI configuration yet. Do **not** assume a language, framework, or architecture — none has been chosen and committed.

> When real code lands, update this file to describe the actual structure, commands, and conventions. Until then, keep the "future conventions" section below as a living checklist rather than treating it as established fact.

## What "meltmarketexchange" appears to be

The repository name suggests a market/exchange application (likely trading or crypto-adjacent). Treat this as an inference, not a specification — confirm the intended scope with the maintainer before making architectural decisions on that basis.

## Git workflow

- **Default branch:** `main`
- **Do not commit directly to `main`.** Develop on a feature branch and open a pull request.
- Push with `git push -u origin <branch-name>`.
- After pushing, open a **draft** pull request if no open PR already exists for the branch.
- Write clear, descriptive commit messages that explain the *why*, not just the *what*.

There is no PR template in the repo yet. If you add one, place it at `.github/pull_request_template.md`.

## Working in an empty repository

When asked to add features to this repo, remember there is no existing scaffolding to build on. Before writing code:

1. Confirm the target language/framework and package manager with the maintainer if it isn't stated in the request.
2. Establish the project skeleton (dependency manifest, source layout, formatter/linter config, test runner) as part of the first substantive change.
3. Add the corresponding commands to the **Development commands** section below so future sessions can build, test, and run without rediscovery.

Avoid introducing tooling, frameworks, or large dependencies unilaterally — surface the choice first when it is consequential.

## Development commands

_None yet — no build tooling exists._ Populate this section as soon as a build/test/run setup is committed. Suggested shape:

```
# Install dependencies
# Run the app locally
# Run tests
# Lint / format
```

## Future conventions (to fill in as the project grows)

Keep this checklist current. Convert each item from "planned" to "documented" once it actually exists in the repo:

- [ ] Language & runtime version
- [ ] Package manager & dependency manifest
- [ ] Source directory layout
- [ ] Build command
- [ ] Test framework & how to run the suite
- [ ] Linter / formatter and their config
- [ ] CI pipeline (e.g. `.github/workflows/`)
- [ ] Environment variables / secrets handling
- [ ] Deployment process

## Notes for AI assistants

- Verify claims against the working tree before stating them — this file describes an empty repo, and that will change.
- Do not fabricate file paths, modules, or commands that don't exist.
- When you establish a new convention (directory layout, test command, lint rule), record it here in the same change so it isn't lost.
