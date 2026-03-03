# SKILL: Reviewer

## Purpose
Monitor open Pull Requests for human review comments, classify each comment, apply the required
changes, push a revised commit, and re-request review — iterating until the PR is approved.

## Trigger
Invoked by the SOP Engine when a PR has new unresolved review comments (GitHub event:
`pull_request_review` or `pull_request_review_comment`).

---

## Inputs

| Field       | Type   | Required | Description |
|-------------|--------|----------|-------------|
| pr_number   | int    | yes      | GitHub PR number |
| pr_url      | string | yes      | GitHub PR URL |
| ticket_id   | string | yes      | Linked JIRA ticket |
| comments    | list   | yes      | List of unresolved review comments |
| iteration   | int    | no       | Current revision iteration (default 1) |

---

## Comment Classification

### BLOCKING
Must be resolved before the PR can be merged:
- Correctness issues (bugs, wrong logic, missing edge cases)
- Security concerns
- Missing test coverage for new code paths
- API contract violations
- Performance regressions

### SUGGESTION
Should be addressed but not strictly required:
- Style improvements
- Better variable naming
- Code organisation improvements
- Documentation additions

### ACKNOWLEDGED
No code change required:
- Questions answered with a comment reply
- Nitpicks explicitly marked as non-blocking
- Compliments or FYIs

---

## Steps

1. **Fetch PR comments** — Use `github_get_pr_comments(pr_number)` to get all unresolved comments.
2. **Filter new comments** — Skip comments already marked as resolved or replied to.
3. **Classify each comment** — Apply classification rules above. For ambiguous comments, check context.
4. **Plan changes** — Group `BLOCKING` and `SUGGESTION` comments by file. Plan the changes before editing.
5. **Checkout branch** — Ensure the local branch is at the latest commit.
6. **Apply BLOCKING changes** — Address each blocking comment. Do not change unrelated code.
7. **Apply SUGGESTION changes** — Address suggestions if they improve clarity without introducing risk.
8. **Reply to ACKNOWLEDGED comments** — Post a GitHub reply: "Acknowledged — no code change required."
9. **Run build and tests** — Verify nothing is broken after changes.
10. **Commit** — Use message: `[TICKET-ID] Address review comments (iteration N)`.
11. **Push** — Push the updated branch.
12. **Re-request review** — Use `github_request_review(pr_number, reviewers)`.
13. **Post summary comment** — Post a GitHub PR comment summarising what was addressed.
14. **Check iteration limit** — If iteration > 2 and comments are still ambiguous, escalate to human.
15. **Emit output message** — Return revision details to SOP Engine.

---

## Ambiguity Detection

A comment is considered ambiguous when:
- It references context not visible in the PR diff.
- It requires architectural decisions (e.g., "should we refactor this entire module?").
- It contradicts the original ticket acceptance criteria.
- Two or more reviewers have left conflicting comments on the same line.

On ambiguity after 2 iterations: transition ticket to `Needs Human Decision`, post a JIRA comment
tagging the tech lead.

---

## Outputs

| Field           | Type   | Description |
|-----------------|--------|-------------|
| pr_number       | int    | GitHub PR number |
| ticket_id       | string | JIRA ticket ID |
| iteration       | int    | Revision number |
| resolved_count  | int    | Number of comments addressed |
| escalated       | bool   | True if human escalation was triggered |
| commit_sha      | string | New HEAD commit SHA |
| status          | string | revised / escalated / approved |

---

## Scripts

- Uses GitHub MCP tools and the same `build.sh` / `test.sh` from the Developer Skill.

---

## Error Handling

| Error | Action |
|-------|--------|
| Comment fetch fails | Retry 3 times, then skip this cycle |
| Build fails after applying changes | Revert last change, post comment asking reviewer to clarify |
| Push rejected (force-push not allowed) | Fetch and rebase, then push |
| Reviewer not available for re-request | Skip re-request, post comment instead |

---

## Summary Comment Template

```markdown
## Review Response — Iteration N

Thanks for the feedback! Here is what was addressed:

### Resolved (Blocking)
- [File:Line] <summary of what was fixed>

### Resolved (Suggestions)
- [File:Line] <summary of what was improved>

### Acknowledged (No Change)
- [Comment]: <explanation>

### Escalated (Needs Human Decision)
- [Comment]: <why this needs a human decision>

Build: ✅ Passing | Tests: ✅ Passing
```
