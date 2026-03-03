# SKILL: Developer / Implementation

## Purpose
Pick up a triaged ticket in `Ready for Dev` state, create a branch, implement the required changes,
run the build and tests, and open a Pull Request — without human involvement.

## Trigger
Invoked by the SOP Engine when a ticket transitions to `Ready for Dev` state.

---

## Inputs

| Field              | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| ticket_id          | string | yes      | JIRA ticket identifier |
| ticket_body        | string | yes      | Full ticket description |
| acceptance_criteria| string | yes      | What done looks like |
| classification     | string | yes      | Must be READY (from Triage output) |
| triage_rationale   | string | no       | Triage Agent's rationale |

---

## Branch Naming Convention

```
<TICKET-ID>/<kebab-case-slug>

Examples:
  PROJ-123/add-user-pagination
  PROJ-456/fix-null-pointer-in-auth
```

The slug is derived from the ticket title: lowercase, spaces replaced with hyphens, max 50 chars.

---

## Commit Message Format

```
[TICKET-ID] <imperative short description (max 72 chars)>

<optional body: what changed and why, wrapped at 72 chars>

Refs: TICKET-ID
```

---

## Steps

1. **Read ticket** — Use `jira_get_ticket(ticket_id)` to load the full context.
2. **Assess complexity** — If ticket seems `COMPLEX` on closer reading, emit message to Researcher Agent and pause.
3. **Create branch** — Use `git_create_branch(branch_name)` following the naming convention.
4. **Draft implementation plan** — Produce a step-by-step plan before writing code. Log the plan.
5. **Implement changes** — Edit source files according to the acceptance criteria.
6. **Run build** — Execute `./scripts/build.sh` (or equivalent). On failure, attempt to fix and retry up to 3 times.
7. **Run tests** — Execute `./scripts/test.sh`. On failure, fix the failing tests (not the tests themselves unless they are wrong) and retry up to 3 times.
8. **Commit** — Use `git_commit(message)` following the commit format.
9. **Push branch** — Use `git_push(branch_name)`.
10. **Open PR** — Use `github_create_pr(title, body, branch, base)`. PR body must include:
    - Link to JIRA ticket
    - Summary of changes
    - Testing notes
    - Any assumptions made
11. **Post PR link** — Use `jira_add_comment(ticket_id, pr_url)`.
12. **Transition ticket** — Use `jira_transition(ticket_id, "Code Review")`.
13. **Emit output message** — Return PR details to SOP Engine.

---

## Implementation Guidelines

- Write the minimal code that satisfies the acceptance criteria. Do not over-engineer.
- Follow the existing code style and patterns in the repository.
- Do not modify unrelated files.
- Do not introduce new dependencies without checking the existing dependency list.
- If you discover a pre-existing bug while implementing, log it as a new JIRA ticket (do not fix it in this PR).

---

## Outputs

| Field        | Type   | Description |
|--------------|--------|-------------|
| ticket_id    | string | JIRA ticket ID |
| branch_name  | string | Created branch name |
| pr_url       | string | GitHub PR URL |
| pr_number    | int    | GitHub PR number |
| commit_sha   | string | HEAD commit SHA |
| test_status  | string | passed / failed |
| new_jira_state | string | "Code Review" |

---

## Scripts

```
scripts/
├── build.sh       # Compile and lint the project
├── test.sh        # Run the test suite
└── branch.sh      # Utility for branch name normalisation
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Build fails after 3 retries | Transition ticket to `Blocked`, post build log excerpt to JIRA |
| Tests fail after 3 retries | Transition ticket to `Blocked`, post test failure summary to JIRA |
| Branch name conflict | Append `-v2`, `-v3` suffix and retry |
| PR creation fails | Log full error, retry once, then escalate to human |
| Complexity discovered mid-implementation | Pause, emit to Researcher Agent, await decision |

---

## PR Body Template

```markdown
## Summary
<One-paragraph description of what was changed and why>

## JIRA Ticket
[TICKET-ID](<jira_url>)

## Changes
- <bullet list of files changed and what was done>

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual smoke test: <describe what was tested>

## Assumptions
<Any assumptions made during implementation>

## Notes for Reviewer
<Anything the reviewer should pay special attention to>
```
