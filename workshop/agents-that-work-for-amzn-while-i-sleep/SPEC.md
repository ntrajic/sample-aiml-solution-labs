# Multi-Agent Ticketing System — Architecture Specification

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CRON / SHELL LOOP                            │
│                     (triggers/cron_trigger.py)                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  schedules
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SOP ENGINE                                   │
│               (orchestration/sop_engine.py)                         │
│  Reads: config/SOP.yaml   Validates hand-off contracts              │
└──────┬──────────┬───────────────────────┬──────────────┬────────────┘
       │          │                       │              │
       ▼          ▼                       ▼              ▼
  [Triage]   [Developer]            [Reviewer]     [Researcher]
  Agent       Agent                  Agent           Agent
       │          │                       │              │
       └──────────┴───────────┬───────────┘              │
                              │                          │
                    ┌─────────▼──────────┐               │
                    │   Message Bus      │◄──────────────┘
                    │  (core/message.py) │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        JIRA MCP         GitHub MCP      Search API
       (mcp/jira)       (mcp/github)    (mcp/search)
```

---

## 2. Package Structure

```
multi-agent-system/
├── pyproject.toml
├── config/
│   └── SOP.yaml                    # Default developer SOP definition
├── skills/
│   ├── TRIAGE_SKILL.md
│   ├── DEVELOPER_SKILL.md
│   ├── REVIEWER_SKILL.md
│   ├── RESEARCHER_SKILL.md
│   └── SOP_SKILL.md
└── src/
    ├── core/                       # PKG-1: Shared primitives
    │   ├── __init__.py
    │   ├── message.py              # Message dataclass
    │   ├── state_machine.py        # Ticket state transitions
    │   └── base_agent.py           # Abstract base for all agents
    ├── agents/                     # PKG-2: Agent implementations
    │   ├── __init__.py
    │   ├── triage_agent.py
    │   ├── developer_agent.py
    │   ├── reviewer_agent.py
    │   └── researcher_agent.py
    ├── mcp/                        # PKG-3: MCP clients
    │   ├── __init__.py
    │   ├── base_client.py          # Retry logic, base HTTP client
    │   ├── jira_client.py
    │   └── github_client.py
    ├── skills_engine/              # PKG-4: Skills loader
    │   ├── __init__.py
    │   ├── skill.py                # Skill dataclass
    │   └── loader.py               # Hot-reload skill loader
    ├── orchestration/              # PKG-5: SOP & runner
    │   ├── __init__.py
    │   ├── sop_engine.py           # YAML SOP interpreter
    │   └── agent_runner.py         # Parallel/sequential runner
    └── triggers/                   # PKG-6: Automation triggers
        ├── __init__.py
        ├── shell_loop.py           # Poll loop (Ralph Wiggum loop)
        └── cron_trigger.py         # Cron job wrapper
```

---

## 3. Core Data Models

### 3.1 TicketState (state_machine.py)

```
BACKLOG → TRIAGE → NEEDS_INFO → TRIAGE (re-entry)
                 → READY_FOR_DEV → IN_PROGRESS → CODE_REVIEW
                                                → CHANGES_REQUESTED → IN_PROGRESS
                                                → APPROVED → DONE
                 → OUT_OF_SCOPE
```

### 3.2 Message Schema

```python
@dataclass
class Message:
    id: str               # UUID
    source_agent: str     # e.g. "triage", "developer"
    target_agent: str     # e.g. "developer", "reviewer", "human"
    ticket_id: str        # JIRA ticket ID
    payload: dict         # Agent-specific structured data
    timestamp: datetime
    correlation_id: str   # Links messages in the same ticket chain
```

### 3.3 SOP Step Schema (YAML)

```yaml
step:
  id: string              # Unique step identifier
  name: string            # Human-readable name
  agent: string           # Agent class name to invoke
  skill: string           # Skill file to load
  inputs:                 # Expected keys from previous step output
    - field: string
      required: bool
  outputs:                # Keys this step must produce
    - field: string
      type: string
  on_success: string      # Next step ID
  on_failure: string      # Fallback step ID or "human_escalation"
  on_condition:           # Optional conditional branching
    field: string
    value: string
    then: string
```

---

## 4. Agent Contract

Every agent extends `BaseAgent` and must implement:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, message: Message, dry_run: bool = False) -> Message:
        """
        Consume an input Message, perform work, return an output Message.
        Must be idempotent: running twice on the same input produces the same output.
        """

    @abstractmethod
    def validate_input(self, message: Message) -> bool:
        """Return True if this agent can handle the given message."""
```

---

## 5. MCP Client Contract

```python
class BaseMCPClient(ABC):
    MAX_RETRIES = 3
    BACKOFF_BASE = 2  # seconds

    @abstractmethod
    async def call(self, tool: str, params: dict) -> dict:
        """Call a single MCP tool with retry + exponential back-off."""
```

---

## 6. Skill Schema

```markdown
# SKILL: <name>

## Purpose
One-sentence description of what this skill does.

## Trigger
When should an agent invoke this skill?

## Inputs
- field_name (type): description

## Steps
1. Step one description
2. Step two description

## Outputs
- field_name (type): description

## Scripts
Reference to bundled .py or .sh scripts.

## Error Handling
What to do on failure.
```

---

## 7. SOP Engine Execution Model

1. Load `SOP.yaml` on startup.
2. Poll message bus for the next pending message.
3. Resolve the current step from the message's `ticket_state`.
4. Validate the message payload against the step's `inputs` schema.
5. Instantiate the step's agent; call `agent.run(message)`.
6. Validate the output message against the step's `outputs` schema.
7. Emit the output message to the bus.
8. Transition the ticket state.
9. If `on_condition` matches, branch; otherwise follow `on_success`.
10. Log the full execution record.

---

## 8. Trigger Architecture

### Shell Loop (Ralph Wiggum Loop)

```
while True:
    work = jira.query(status="Ready for Dev")
    if work:
        for ticket in work:
            agent_runner.run(ticket)   # fresh context per ticket
    else:
        sleep(SLEEP_SECONDS)
```

### Cron Trigger

Wraps the shell loop as a one-shot invocation suitable for cron scheduling:

```
*/15 * * * *  /usr/local/bin/python -m triggers.cron_trigger
```

---

## 9. Environment Variables

| Variable             | Description |
|----------------------|-------------|
| JIRA_BASE_URL        | JIRA instance base URL |
| JIRA_API_TOKEN       | JIRA API token |
| JIRA_PROJECT_KEY     | Target project key |
| GITHUB_TOKEN         | GitHub personal access token |
| GITHUB_REPO          | owner/repo format |
| ANTHROPIC_API_KEY    | LLM provider key |
| AGENT_DRY_RUN        | Set to "1" to run without side effects |
| LOOP_SLEEP_SECONDS   | Polling interval (default: 60) |
| SOP_CONFIG_PATH      | Path to SOP.yaml (default: config/SOP.yaml) |

---

## 10. Logging Schema

Every agent action emits a JSON log line:

```json
{
  "ts": "2026-02-07T10:00:00Z",
  "level": "INFO",
  "agent": "developer",
  "ticket_id": "PROJ-123",
  "step": "create_branch",
  "correlation_id": "uuid",
  "duration_ms": 1234,
  "status": "success",
  "payload": {}
}
```
