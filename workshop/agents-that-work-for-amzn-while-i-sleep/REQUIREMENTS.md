# Multi-Agent Ticketing System — Requirements

## 1. Overview

This document defines the full functional and non-functional requirements for an autonomous
multi-agent system that processes JIRA tickets end-to-end: from triage through implementation,
code review, and PR merge — with a human reviewer in the final approval gate.

---

## 2. Goals

| ID  | Goal |
|-----|------|
| G-1 | Eliminate the human as the "start button" for routine ticket work |
| G-2 | Eliminate the human as the "glue" between JIRA, GitHub, and the LLM |
| G-3 | Preserve human judgment at architectural, ambiguous, and final-approval stages |
| G-4 | Maintain reliability through specialised agents with narrow, well-defined scopes |
| G-5 | Enable continuous operation via cron-scheduled shell loops |

---

## 3. Functional Requirements

### 3.1 Triage Agent

| ID    | Requirement |
|-------|-------------|
| TR-1  | SHALL query the JIRA backlog on each execution cycle |
| TR-2  | SHALL classify each ticket as `Ready`, `NeedsInfo`, or `OutOfScope` |
| TR-3  | SHALL post a comment on JIRA with the classification rationale |
| TR-4  | SHALL transition tickets to the `Ready for Dev` state when classification is `Ready` |
| TR-5  | SHALL post a clarification request comment when classification is `NeedsInfo` |
| TR-6  | SHALL NOT modify source code or create branches |
| TR-7  | SHALL output a structured triage report consumed by the Developer Agent |

### 3.2 Developer Agent

| ID    | Requirement |
|-------|-------------|
| DEV-1 | SHALL only pick up tickets in state `Ready for Dev` |
| DEV-2 | SHALL create a feature branch following the naming convention `<ticket-id>/<slug>` |
| DEV-3 | SHALL implement changes according to the ticket acceptance criteria |
| DEV-4 | SHALL run the local build/test suite and retry up to 3 times on failure |
| DEV-5 | SHALL commit with a message format: `[TICKET-ID] <short description>` |
| DEV-6 | SHALL open a Pull Request and post the PR URL as a JIRA comment |
| DEV-7 | SHALL transition the JIRA ticket to `Code Review` after PR creation |
| DEV-8 | SHALL NOT approve or merge its own PRs |

### 3.3 Reviewer Agent

| ID    | Requirement |
|-------|-------------|
| REV-1 | SHALL monitor open PRs for new human review comments |
| REV-2 | SHALL classify each comment as `Blocking`, `Suggestion`, or `Acknowledged` |
| REV-3 | SHALL apply `Blocking` and `Suggestion` changes to the branch |
| REV-4 | SHALL push a revised commit and re-request review |
| REV-5 | SHALL post a response comment explaining what was changed and why |
| REV-6 | SHALL escalate to a human when a comment is ambiguous after 2 iterations |
| REV-7 | SHALL NOT self-approve PRs |

### 3.4 Researcher Agent

| ID    | Requirement |
|-------|-------------|
| RES-1 | SHALL be invoked when the Developer Agent classifies a ticket as `Complex` |
| RES-2 | SHALL search internal documentation, external docs, and code history |
| RES-3 | SHALL produce a structured options report (min 2, max 5 alternatives) |
| RES-4 | SHALL attach trade-off analysis (complexity, risk, time) to each option |
| RES-5 | SHALL post the report as a JIRA comment and await human selection |
| RES-6 | SHALL NOT make implementation decisions autonomously |

### 3.5 Orchestration / SOP Engine

| ID    | Requirement |
|-------|-------------|
| ORC-1 | SHALL load a YAML-defined SOP at startup |
| ORC-2 | SHALL route tickets between agents based on ticket state transitions |
| ORC-3 | SHALL enforce hand-off contracts (output schema validation) between agents |
| ORC-4 | SHALL maintain an execution log for every agent action |
| ORC-5 | SHALL support parallel execution of independent agent tasks |
| ORC-6 | SHALL provide a dry-run mode that simulates execution without side effects |

### 3.6 Shell Loop & Automation Trigger

| ID    | Requirement |
|-------|-------------|
| SHL-1 | SHALL implement a poll loop that queries for work and exits cleanly when none exists |
| SHL-2 | SHALL support a configurable --sleep-seconds interval |
| SHL-3 | SHALL support cron-based scheduling as an alternative to the sleep loop |
| SHL-4 | SHALL emit structured JSON logs for each run to stdout |
| SHL-5 | SHALL handle SIGTERM gracefully, completing the current task before exit |

---

## 4. Non-Functional Requirements

| ID    | Category       | Requirement |
|-------|----------------|-------------|
| NF-1  | Reliability    | Each agent SHALL retry transient failures up to 3 times with exponential back-off |
| NF-2  | Observability  | All inter-agent messages SHALL be logged with timestamp, agent, and payload |
| NF-3  | Security       | API credentials SHALL be loaded from environment variables only |
| NF-4  | Idempotency    | Re-running an agent on the same ticket SHALL produce the same outcome |
| NF-5  | Extensibility  | Adding a new agent SHALL require only a new class + SOP YAML entry |
| NF-6  | Testability    | All agents SHALL expose a dry_run mode with mocked MCP clients |
| NF-7  | Performance    | A single ticket cycle (triage to PR) SHALL complete within 10 minutes |

---

## 5. Integration Requirements

| System   | Requirement |
|----------|-------------|
| JIRA     | Read/write tickets, comments, state transitions via JIRA MCP |
| GitHub   | Create branches, commits, PRs, read review comments via GitHub MCP |
| Local FS | Read/write source files, run build scripts via shell skills |
| Search   | Query internal docs and external APIs for the Researcher Agent |

---

## 6. Human-in-the-Loop Requirements

| ID    | Requirement |
|-------|-------------|
| HIL-1 | A human MUST provide final PR approval before merge |
| HIL-2 | A human MAY intervene at any state transition |
| HIL-3 | Ambiguous triage classifications SHALL be escalated to a human within 1 cycle |
| HIL-4 | Researcher option selection SHALL always require explicit human choice |
| HIL-5 | The system SHALL surface a clear escalation path in every JIRA comment |

---

## 7. Out of Scope

- Automated production deployments
- Security vulnerability patching without human review
- Agent self-modification of SOP or skill files
