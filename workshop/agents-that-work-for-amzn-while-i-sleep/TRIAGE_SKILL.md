# SKILL: Triage

## Purpose
Inspect the JIRA backlog, classify each ticket, and transition it to the correct downstream state so
the Developer Agent can pick it up without human intervention.

## Trigger
Invoked by the SOP Engine at the start of each poll cycle when tickets are found in `BACKLOG` or
`TRIAGE` state.

---

## Inputs

| Field          | Type   | Required | Description |
|----------------|--------|----------|-------------|
| ticket_id      | string | yes      | JIRA ticket identifier |
| ticket_title   | string | yes      | Short title of the ticket |
| ticket_body    | string | yes      | Full ticket description |
| acceptance_criteria | string | no | Acceptance criteria if present |
| attachments    | list   | no       | File attachments or links |

---

## Classification Rules

### READY
All of the following must be true:
- The ticket has a clear, unambiguous description.
- Acceptance criteria are explicitly stated or can be inferred with high confidence.
- The scope of change is limited to ≤ 3 files or 1 logical component.
- No external dependency decisions are pending.
- No waiting-on-human flags exist.

### NEEDS_INFO
Classify as `NEEDS_INFO` when any of the following are true:
- Description is vague or missing context about the expected behaviour.
- Acceptance criteria are absent and cannot be inferred.
- The ticket references another ticket that is still open/unresolved.
- There is a conflict between the title and the body.
- A specific data format or schema is referenced but not provided.

### OUT_OF_SCOPE
Classify as `OUT_OF_SCOPE` when any of the following are true:
- The ticket requires a production deployment decision.
- The ticket involves security-sensitive changes (auth, secrets, permissions).
- The ticket involves schema migrations without a migration plan.
- The ticket description explicitly mentions architectural redesign.

### COMPLEX
Classify as `COMPLEX` (routes to Researcher Agent) when:
- Multiple implementation approaches are plausible and trade-offs are non-trivial.
- External library evaluation is needed.
- Performance or scaling implications are significant.

---

## Steps

1. **Fetch ticket** — Use `jira_get_ticket(ticket_id)` to retrieve the full ticket payload.
2. **Parse fields** — Extract title, body, acceptance criteria, labels, and linked tickets.
3. **Check linked tickets** — If linked tickets are `In Progress` or `Blocked`, classify `NEEDS_INFO`.
4. **Apply classification rules** — Follow the rules above in order: `OUT_OF_SCOPE` → `COMPLEX` → `NEEDS_INFO` → `READY`.
5. **Write rationale** — Produce a one-paragraph rationale for the classification.
6. **Post JIRA comment** — Use `jira_add_comment(ticket_id, comment)` with the rationale.
7. **Transition ticket state** — Use `jira_transition(ticket_id, target_state)`:
   - `READY` → transition to `Ready for Dev`
   - `NEEDS_INFO` → transition to `Waiting for Info`, post clarification questions
   - `OUT_OF_SCOPE` → transition to `Out of Scope`, tag the reporter
   - `COMPLEX` → transition to `Research Needed`, emit message to Researcher Agent
8. **Emit output message** — Return structured triage result to SOP Engine.

---

## Outputs

| Field           | Type   | Description |
|-----------------|--------|-------------|
| ticket_id       | string | JIRA ticket ID |
| classification  | enum   | READY / NEEDS_INFO / OUT_OF_SCOPE / COMPLEX |
| rationale       | string | One-paragraph explanation |
| clarifications  | list   | Questions posted if NEEDS_INFO |
| jira_comment_id | string | ID of the posted comment |
| new_state       | string | JIRA state after transition |

---

## Scripts

- None required. Uses JIRA MCP tools exclusively.

---

## Error Handling

| Error | Action |
|-------|--------|
| JIRA API timeout | Retry up to 3 times with exponential back-off (2s, 4s, 8s) |
| Ticket not found | Log warning, skip ticket, continue cycle |
| Transition rejected (invalid workflow) | Log error, post comment asking human to check workflow config |
| LLM classification confidence < 0.7 | Default to `NEEDS_INFO` and escalate to human |

---

## Example JIRA Comment (READY)

```
🤖 Triage Agent — Classification: READY

This ticket has a clear description, explicit acceptance criteria, and is scoped
to a single component. No blockers or dependencies detected.

Moving to: Ready for Dev
```

## Example JIRA Comment (NEEDS_INFO)

```
🤖 Triage Agent — Classification: NEEDS_INFO

The ticket description does not specify the expected output format for the API response.
The following clarifications are needed:

1. Should the endpoint return paginated results? If so, what page size?
2. Is authentication required for this endpoint?
3. Which error codes should be returned for invalid input?

Please update the ticket and it will be re-triaged automatically.
```
