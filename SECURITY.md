# Security Policy

RePoG is a local workspace made of Markdown templates, workflows, and small
Python helper tools.

## Supported Versions

Security reports are accepted for the current `main` branch and the latest
tagged release.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if available, or contact the
maintainer through GitHub with:

- a short description of the issue;
- affected files or commands;
- steps to reproduce;
- expected impact;
- any safe suggested fix.

Do not publicly post working exploit details before the maintainer has had a
reasonable chance to respond.

## Current Security Boundaries

- RePoG should not require secrets or API keys for normal use.
- Helper tools should stay local and deterministic.
- Campaign content can contain user-written material; do not run untrusted
  generated scripts from a campaign folder.
- Agentic tools may have their own filesystem and network permissions. Review
  those permissions before using any agent with a campaign that contains
  private notes.
