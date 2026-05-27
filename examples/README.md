# Examples

## python_client.py

End-to-end demonstration of the API from Python: register, create project, add tasks, query stats, export CSV.

```bash
# 1. Start the API
uvicorn app.main:app --reload

# 2. In another terminal
pip install httpx
python examples/python_client.py
```

Outputs something like:

```
Registering demo+1716816000@example.com...
  access_token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
  /auth/me -> id=1 email=demo+1716816000@example.com

Creating project 'Sprint 14'...
  project_id=1

Adding 3 tasks via bulk endpoint...
  created 3 tasks

All tasks in project:
  [todo       ] high   Design auth flow          tags=[design,auth]
  [in_progress] medium Wire up CI                tags=[-]
  [done       ] low    Write docs                tags=[-]

Project stats:
  total: 3
  by_status: {'todo': 1, 'in_progress': 1, 'done': 1}
  by_priority: {'high': 1, 'medium': 1, 'low': 1}
  overdue: 0

Exporting CSV:
  saved to sprint_1_tasks.csv (483 bytes)

Done.
```

### Configuration

Set `TASKLY_API` to point at a different host:

```bash
TASKLY_API=https://taskly.example.com python examples/python_client.py
```
