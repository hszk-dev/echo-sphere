# EchoSphere - AI Agent Instructions

This file provides context for AI agents (Claude Code, Cursor, etc.) working on this project.

## Agent Behavior

### Action Mode
Implement changes directly rather than suggesting them. If intent is unclear, proceed with the most useful action.

### Parallel Execution
Execute independent tool calls in parallel to maximize efficiency.

### Grounded Responses
Read code before making statements about it. Do not guess about files you haven't inspected.

### Context Management
Do not stop early due to token concerns. For multi-context tasks, use JSON state files and git commits to track progress.

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

## Critical Rules

### Language Policy
Write all code, comments, documentation, commits, and logs in English.

### Architecture Boundaries
- Keep `domain/` layer pure Python with zero external package imports
- Make features self-contained with no circular dependencies
- Access all external services through adapter implementations

### Code Quality
- Use specific types in TypeScript (use `unknown` instead of `any` for truly unknown types)
- Use async I/O in Python (`httpx` for HTTP, `aiofiles` for files, `asyncio.sleep` for delays)
- Keep business logic in domain/application layers; adapters handle only I/O
- Load configuration from environment variables via pydantic-settings
- Store secrets in environment variables only (validated by CI)
- Write tests for all domain logic before considering work complete

## File Organization

When creating new files:
- Backend features → `apps/agent/src/`
- Frontend features → `apps/web/src/features/<name>/`
- Shared UI → `apps/web/src/shared/components/`
- Types → Co-locate with feature or in `shared/types/`
- Tests → Adjacent to source (`__tests__/` or `.test.ts`)
- ADRs → `docs/adr/NNN-title.md`

## Before You Code

1. Check existing patterns in the codebase
2. Read the relevant ADR if one exists
3. Ensure the Issue/RFC is clear
4. Write or update tests alongside code
5. Run `task check` before committing

## Verification Questions

Before completing any task, verify:
- Correct architectural layer?
- Tests written and passing?
- Existing functionality preserved?
- Error handling appropriate?
- Observability in place (logging, tracing)?

## Individual Preferences

Team members can add personal preferences by creating:
@~/.claude/echo-sphere.md
