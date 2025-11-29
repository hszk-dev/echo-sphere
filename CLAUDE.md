# EchoSphere - AI Agent Instructions

This file provides context for AI agents (Claude Code, Cursor, etc.) working on this project.

## Quick Reference

See @README.md for project overview and available commands.

```bash
task dev          # Start all services
task check        # Run linters and type checkers
task test         # Run all tests
task fix          # Auto-fix linting issues
```

## Project Documentation

- Project overview and setup: @README.md
- Development workflow and coding standards: @CONTRIBUTING.md
- Technology stack and versions: @docs/architecture/tech-stack.md
- System architecture: @docs/architecture/system-overview.md
- Architecture decisions: @docs/adr/001-system-architecture.md

## Critical Rules (DO NOT VIOLATE)

### Language Policy
- All code, comments, documentation, commits, and logs MUST be in English

### Architecture Boundaries
- `domain/` must have NO imports from external packages
- Features must be self-contained with no circular dependencies
- All external services accessed through adapters

### Code Quality
- Never use `any` type in TypeScript
- Never use blocking I/O in Python (`requests`, `time.sleep`)
- Never put business logic in adapters
- Never hardcode configuration values
- Never commit secrets or API keys
- Never skip tests for domain logic

## File Organization

When creating new files:
- Backend features → `apps/agent/src/`
- Frontend features → `apps/web/src/features/<name>/`
- Shared UI → `apps/web/src/shared/components/`
- Types → Co-locate with feature or in `shared/types/`
- Tests → Adjacent to source (`__tests__/` or `.test.ts`)
- ADRs → `docs/adr/NNN-title.md`

## Before You Code

1. Check if there's an existing pattern in the codebase
2. Read the relevant ADR if one exists
3. Ensure the Issue/RFC is clear
4. Write or update tests alongside code
5. Run `task check` before committing

## Questions to Ask Yourself

- Is this in the right architectural layer?
- Are there tests for this logic?
- Will this break existing functionality?
- Is the error handling appropriate?
- Is this observable (logging, tracing)?

## Individual Preferences

Team members can add personal preferences by creating:
@~/.claude/echo-sphere.md
