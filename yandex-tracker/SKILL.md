---
name: yandex-tracker
description: >
  Manage Yandex Tracker issues, comments, attachments, links, queues, boards, sprints,
  worklogs, checklists, bulk operations, versions, components, fields, and filters via CLI.
  Use when: (1) creating, updating, or searching issues in Yandex Tracker, (2) managing
  comments and attachments on issues, (3) executing transitions (status changes),
  (4) bulk-updating or moving issues, (5) listing queues, boards, sprints, or versions,
  (6) tracking work time via worklogs, (7) managing issue links and checklists.
  Triggers on: Yandex Tracker, трекер, задачи трекера, тикеты, очереди трекера.
---

# Yandex Tracker

CLI wrapper around `yandex_tracker_client` Python library.

## Prerequisites

Install dependencies:

```bash
pip install -r scripts/requirements.txt
```

Set environment variables — see [references/setup.md](references/setup.md) for detailed auth guide.

Required env vars (choose one auth method):

- `YANDEX_TRACKER_TOKEN` + `YANDEX_TRACKER_ORG_ID` — OAuth token
- `YANDEX_TRACKER_TOKEN` + `YANDEX_TRACKER_CLOUD_ORG_ID` — OAuth + Cloud org
- `YANDEX_TRACKER_IAM_TOKEN` + `YANDEX_TRACKER_CLOUD_ORG_ID` — IAM token (Cloud only)

## Usage

All commands output JSON by default. Use `--format text` for plain text.

```bash
python3 scripts/tracker.py <command> <action> [args]
```

## Commands Reference

### Issues

```bash
# Get issue
tracker.py issue get QUEUE-42

# Create issue
tracker.py issue create --queue QUEUE --summary "Bug title" --type Bug --description "Details" --assignee user --priority critical

# Update issue
tracker.py issue update QUEUE-42 --summary "New title" --assignee other_user --field tags='["urgent"]'

# Search (tracker query language)
tracker.py issue search --query "Queue: MYQUEUE Assignee: me()"

# Search with filter
tracker.py issue search --filter queue=MYQUEUE assignee=me() --per-page 20 --order -updated +priority

# Count matching issues
tracker.py issue count --query "Queue: MYQUEUE Status: open"

# List available transitions
tracker.py issue transitions QUEUE-42

# Execute transition (change status)
tracker.py issue transition QUEUE-42 close --comment "Fixed" --resolution fixed

# Move to another queue
tracker.py issue move QUEUE-42 NEWQUEUE

# Clone issue
tracker.py issue clone QUEUE-42 NEWQUEUE --all-fields --link

# View changelog
tracker.py issue changelog QUEUE-42
```

### Comments

```bash
tracker.py comment list QUEUE-42
tracker.py comment create QUEUE-42 --text "Done"
tracker.py comment create QUEUE-42 --text "With files" --attachments file1.png file2.pdf
tracker.py comment update QUEUE-42 123 --text "Updated text"
tracker.py comment delete QUEUE-42 123
```

### Attachments

```bash
tracker.py attachment list QUEUE-42
tracker.py attachment upload QUEUE-42 report.pdf
tracker.py attachment download QUEUE-42 report.pdf --dest /tmp
tracker.py attachment delete QUEUE-42 report.pdf
```

### Links

```bash
tracker.py link list QUEUE-42
tracker.py link create QUEUE-42 OTHER-99 --relationship "is dependent by"
tracker.py link delete QUEUE-42 456
tracker.py link remote-create QUEUE-42 --origin github --remote-key org/repo#123 --relationship relates
```

### Queues

```bash
tracker.py queue list
tracker.py queue list --limit 5
tracker.py queue get MYQUEUE
```

### Bulk Operations

```bash
# Bulk update fields
tracker.py bulk update QUEUE-1 QUEUE-2 QUEUE-3 --field priority=minor tags='{"add":["batch"]}' --wait

# Bulk transition
tracker.py bulk transition QUEUE-1 QUEUE-2 --transition close --wait

# Bulk move
tracker.py bulk move QUEUE-1 QUEUE-2 --queue NEWQUEUE --wait
```

### Worklog

```bash
tracker.py worklog list QUEUE-42
tracker.py worklog create QUEUE-42 --start "2024-03-15T10:00:00" --duration "PT2H30M" --comment "Code review"
```

### Checklists

```bash
tracker.py checklist list QUEUE-42
tracker.py checklist add QUEUE-42 --text "Review PR" --assignee user --deadline 2024-04-01
```

### Users

```bash
tracker.py user me
tracker.py user get some_login
```

### Boards & Sprints

```bash
tracker.py board list
tracker.py board get 42
tracker.py board sprints 42
```

### Versions, Components, Fields, Filters

```bash
tracker.py version list
tracker.py version get 60031
tracker.py component list
tracker.py field list
tracker.py filter list
tracker.py filter get 123
```

## Extra Fields

Use `--field key=value` for any field not covered by named flags. Values are auto-parsed as JSON when possible:

```bash
tracker.py issue create --queue Q --summary "Test" --field fixVersions='[{"name":"v2.0"}]' components='[{"name":"Backend"}]'
```

## Error Handling

- Missing env vars → clear error message with required variable names
- Issue not found → exit code 1 with message
- Auth failures → check token validity and org_id
- All errors print to stderr; successful output goes to stdout
