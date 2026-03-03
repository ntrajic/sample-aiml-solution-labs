# SKILL: Researcher

## Purpose
Explore implementation alternatives for complex tickets, produce a structured trade-off analysis,
and present the options to a human for a final decision — before any code is written.

## Trigger
Invoked when:
- The Triage Agent classifies a ticket as `COMPLEX`.
- The Developer Agent discovers unexpected complexity mid-implementation and pauses.

---

## Inputs

| Field           | Type   | Required | Description |
|-----------------|--------|----------|-------------|
| ticket_id       | string | yes      | JIRA ticket identifier |
| ticket_body     | string | yes      | Full ticket description |
| complexity_note | string | no       | Note from Triage or Developer explaining why research is needed |
| constraints     | list   | no       | Known constraints (e.g., "must not change public API") |

---

## Research Sources (in priority order)

1. **Internal codebase** — Existing patterns, similar implementations, prior art in the repo.
2. **Internal documentation** — Architecture docs, ADRs (Architecture Decision Records), wikis.
3. **JIRA history** — Previous tickets that tackled similar problems.
4. **Official library docs** — Primary documentation for any libraries involved.
5. **External sources** — Engineering blogs, RFC documents, benchmark reports.

---

## Steps

1. **Parse the problem** — Identify the core technical question that needs answering.
2. **Define constraints** — List hard constraints (must-haves) and soft constraints (nice-to-haves).
3. **Search internal codebase** — Use file system tools to find similar implementations.
4. **Search internal docs** — Query the internal documentation database.
5. **Search external sources** — Use Search API for relevant patterns, libraries, benchmarks.
6. **Generate options** — Produce between 2 and 5 distinct implementation approaches.
7. **Analyse trade-offs** — For each option, score: complexity (1–5), risk (1–5), time (hours).
8. **Write recommendation** — Identify the option the agent would choose and briefly explain why.
   Note: this is advisory only — the human makes the final decision.
9. **Post to JIRA** — Use `jira_add_comment` to post the full options report.
10. **Transition ticket** — Move to `Awaiting Decision`.
11. **Emit output message** — Return the options report; await human selection.

---

## Options Report Format

Each option must include:

| Field           | Description |
|-----------------|-------------|
| option_id       | A, B, C... |
| title           | Short descriptive name |
| description     | 2–3 sentences explaining the approach |
| pros            | Bullet list of advantages |
| cons            | Bullet list of disadvantages |
| complexity      | 1 (trivial) to 5 (very complex) |
| risk            | 1 (low) to 5 (high) |
| estimated_hours | Rough time estimate |
| references      | Links or doc references |

---

## Outputs

| Field            | Type   | Description |
|------------------|--------|-------------|
| ticket_id        | string | JIRA ticket ID |
| options          | list   | List of option objects |
| recommendation   | string | Option ID the agent recommends |
| rationale        | string | Why this option is recommended |
| jira_comment_id  | string | Posted comment ID |
| awaiting_human   | bool   | Always true — human must select |

---

## Scripts

- `scripts/search_codebase.sh <query>` — Search source files for patterns.
- Uses Search API MCP tool for external research.

---

## Error Handling

| Error | Action |
|-------|--------|
| No viable options found | Post to JIRA: "No clear path identified — requesting architectural guidance." Escalate. |
| Search API unavailable | Fall back to internal sources only; note limitation in report |
| Fewer than 2 options | Do not post; attempt deeper research before concluding |

---

## Example JIRA Comment

```
🤖 Researcher Agent — Options Report

**Problem**: The ticket requires rate-limiting the public API, but three different
approaches are viable. Human input is needed before implementation begins.

---

**Option A: In-memory token bucket (per-instance)**
- Complexity: 2 | Risk: 3 | Estimate: 4h
- Pros: Simple, fast, no infrastructure changes
- Cons: Does not work correctly with multiple instances; resets on deploy
- Ref: https://en.wikipedia.org/wiki/Token_bucket

**Option B: Redis-backed sliding window**
- Complexity: 3 | Risk: 2 | Estimate: 8h
- Pros: Accurate, horizontally scalable, survives restarts
- Cons: Adds Redis dependency; requires ops involvement for provisioning
- Ref: Internal ADR-042 (Redis adoption)

**Option C: API Gateway rate limiting**
- Complexity: 1 | Risk: 1 | Estimate: 2h
- Pros: Zero code change; managed by infra team
- Cons: Less flexible; requires coordination with platform team
- Ref: Internal wiki > Platform > API Gateway

---

**Agent Recommendation**: Option B — balances accuracy and scalability without
adding architectural risk. Option C is worth discussing with the platform team first.

Please reply to this comment with your chosen option (A, B, or C) to proceed.
```
