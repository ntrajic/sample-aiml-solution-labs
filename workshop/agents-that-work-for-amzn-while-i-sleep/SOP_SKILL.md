# SKILL: Standard Operating Procedure (SOP)

## Purpose
This meta-skill defines the canonical order of operations for the multi-agent ticketing system.
It tells each agent when to invoke which skill, how to hand off to the next agent, and when to
escalate to a human. The SOP is the orchestrator — all other skills are its components.

---

## System Entry Points

The SOP has two entry points depending on the trigger:

| Entry Point        | Trigger |
|--------------------|---------|
| `triage_cycle`     | Cron job or shell loop detects unprocessed tickets in BACKLOG |
| `review_cycle`     | Cron job or shell loop detects new unresolved PR review comments |

---

## Full SOP Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        TRIAGE CYCLE                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. FETCH BACKLOG                                                │
│     Agent: Triage | Skill: TRIAGE_SKILL.md                      │
│     Input: JIRA backlog query                                    │
│     Output: List of unprocessed ticket IDs                       │
│                                                                  │
│  2. CLASSIFY TICKET (per ticket)                                 │
│     Agent: Triage | Skill: TRIAGE_SKILL.md (Steps 1–7)          │
│     Output: classification ∈ {READY, NEEDS_INFO, OUT_OF_SCOPE,  │
│             COMPLEX}                                             │
│                                                                  │
│  ┌─── if READY ──────────────────────────────────────────────┐  │
│  │  3a. IMPLEMENT                                             │  │
│  │      Agent: Developer | Skill: DEVELOPER_SKILL.md         │  │
│  │      Output: PR URL, branch name, commit SHA               │  │
│  │                                                            │  │
│  │  4a. AWAIT REVIEW (human gate)                             │  │
│  │      Human reviews PR, leaves comments or approves         │  │
│  │                                                            │  │
│  │  5a. ADDRESS REVIEW (if comments)                          │  │
│  │      Agent: Reviewer | Skill: REVIEWER_SKILL.md           │  │
│  │      Output: revised PR, re-request review                 │  │
│  │      Loop back to 4a until approved                        │  │
│  │                                                            │  │
│  │  6a. DONE                                                  │  │
│  │      Ticket transitions to DONE after PR merge             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── if COMPLEX ────────────────────────────────────────────┐  │
│  │  3b. RESEARCH                                              │  │
│  │      Agent: Researcher | Skill: RESEARCHER_SKILL.md       │  │
│  │      Output: Options report posted to JIRA                 │  │
│  │                                                            │  │
│  │  4b. AWAIT HUMAN DECISION (human gate)                     │  │
│  │      Human selects option in JIRA comment                  │  │
│  │                                                            │  │
│  │  5b. IMPLEMENT (with selected approach)                    │  │
│  │      Continues at step 3a above                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── if NEEDS_INFO ─────────────────────────────────────────┐  │
│  │  3c. AWAIT HUMAN INPUT (human gate)                        │  │
│  │      Ticket stays in Waiting for Info                      │  │
│  │      On next cycle: re-enter at step 2                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── if OUT_OF_SCOPE ───────────────────────────────────────┐  │
│  │  3d. ESCALATE TO HUMAN                                     │  │
│  │      Ticket transitions to Out of Scope                    │  │
│  │      No further agent action                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       REVIEW CYCLE                               │
├──────────────────────────────────────────────────────────────────┤
│  1. FETCH OPEN PRS WITH COMMENTS                                 │
│     Agent: Reviewer | Tool: github_get_prs_with_comments         │
│     Output: List of PR numbers with unresolved comments          │
│                                                                  │
│  2. ADDRESS COMMENTS (per PR)                                    │
│     Agent: Reviewer | Skill: REVIEWER_SKILL.md                  │
│     Output: revised PR or escalation                             │
│                                                                  │
│  3. RE-REQUEST REVIEW                                            │
│     Agent: Reviewer | Tool: github_request_review                │
│     Loop back to AWAIT REVIEW in triage cycle                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## State Machine

```
BACKLOG
  └─[Triage]──► READY_FOR_DEV ──[Developer]──► CODE_REVIEW
                                                    │
                                      ┌─────────────┤
                                      │             │
                               [human approved] [human comments]
                                      │             │
                                    DONE    CHANGES_REQUESTED
                                                    │
                                              [Reviewer]
                                                    │
                                             CODE_REVIEW (loop)

BACKLOG ──[Triage]──► NEEDS_INFO ──[human updates]──► BACKLOG (re-triage)
BACKLOG ──[Triage]──► OUT_OF_SCOPE (terminal)
BACKLOG ──[Triage]──► RESEARCH_NEEDED ──[Researcher]──► AWAITING_DECISION
                                                              │
                                                      [human selects]
                                                              │
                                                       READY_FOR_DEV
```

---

## Hand-Off Contracts

Each agent must output a valid message before the SOP Engine advances the workflow.

| From → To              | Required Output Fields |
|------------------------|------------------------|
| Triage → Developer     | ticket_id, classification=READY |
| Triage → Researcher    | ticket_id, classification=COMPLEX, complexity_note |
| Developer → Reviewer   | ticket_id, pr_number, pr_url, branch_name |
| Researcher → Human     | ticket_id, options (list, min 2), awaiting_human=true |
| Human → Developer      | ticket_id, selected_option (if from Researcher flow) |
| Reviewer → Human Gate  | ticket_id, pr_number, iteration, status |

---

## Human Gates

The SOP pauses at these points and waits for explicit human action:

| Gate ID  | Trigger                        | Human Action Required |
|----------|--------------------------------|-----------------------|
| HG-1     | PR opened by Developer Agent   | Approve or comment on PR |
| HG-2     | Options report posted by Researcher | Reply with option selection in JIRA |
| HG-3     | Ticket classified NEEDS_INFO   | Update ticket with missing information |
| HG-4     | Reviewer escalation (iteration > 2) | Resolve ambiguous comment |
| HG-5     | Ticket classified OUT_OF_SCOPE | Decide how to handle or close ticket |

---

## SOP Invocation Examples

```bash
# Run one full triage cycle
python -m orchestration.sop_engine --entry triage_cycle

# Run one review cycle
python -m orchestration.sop_engine --entry review_cycle

# Run in dry-run mode (no side effects)
python -m orchestration.sop_engine --entry triage_cycle --dry-run

# Process a specific ticket only
python -m orchestration.sop_engine --entry triage_cycle --ticket PROJ-123
```

---

## SOP Configuration

The SOP is defined in `config/SOP.yaml`. To override defaults:

```yaml
# config/SOP.yaml
sop:
  version: "1.0"
  entry_points:
    - triage_cycle
    - review_cycle
  agents:
    triage:
      skill: skills/TRIAGE_SKILL.md
      max_tickets_per_cycle: 10
    developer:
      skill: skills/DEVELOPER_SKILL.md
      max_retries: 3
    reviewer:
      skill: skills/REVIEWER_SKILL.md
      max_iterations: 3
    researcher:
      skill: skills/RESEARCHER_SKILL.md
  human_gates:
    timeout_hours: 48    # Escalate if gate not resolved within 48h
    reminder_hours: 24   # Post reminder comment after 24h
```
