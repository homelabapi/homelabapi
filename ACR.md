---
rating: B1b
spec: "0.1"
updated: 2026-10-12
---

# AI Code Rating

**ACR B1b** (Maintainer: Experienced · AI Share: 1–25% · Oversight: Reviewed)

This project is rated with [AI Code Rating](https://aicoderating.com/spec/0.1/), spec version 0.1.

## How AI Was Used

Greg Chetcuti wrote almost all of HomelabAPI's code by hand, before AI coding tools were part of the project. Since October 2026, Claude Code has written some changes, starting with URL parameter support for the `/input` endpoint, and including the v0.10.0 upgrade to Python 3.14, FastAPI 0.143, and Pydantic 2. It has also helped with documentation such as `CLAUDE.md`. Greg decides what gets built and reviews all of the AI-written code before it's committed, and changes are tested by running the app. The upgrade was also checked with a smoke test that compares every endpoint's behaviour against the previous release.

Codex also reviews changes before they're committed. That's an AI review, so it doesn't change the oversight level.
