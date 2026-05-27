"""End-to-end example: register, create a project, add tasks, get stats.

Run this against a local instance (uvicorn app.main:app --reload):
    python examples/python_client.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

import httpx

API = os.environ.get("TASKLY_API", "http://localhost:8000")


def register_or_login(client: httpx.Client, email: str, password: str) -> dict:
    r = client.post(f"{API}/auth/register", json={"email": email, "password": password})
    if r.status_code == 409:
        r = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()


def main() -> None:
    email = f"demo+{int(datetime.now().timestamp())}@example.com"
    password = "demo-password-123"

    with httpx.Client(timeout=10) as client:
        # 1. Register
        print(f"Registering {email}...")
        tokens = register_or_login(client, email, password)
        access = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access}"}
        print(f"  access_token: {access[:30]}...")

        # 2. Confirm whoami
        me = client.get(f"{API}/auth/me", headers=headers).json()
        print(f"  /auth/me -> id={me['id']} email={me['email']}")

        # 3. Create a project
        print("\nCreating project 'Sprint 14'...")
        project = client.post(
            f"{API}/projects",
            json={"name": "Sprint 14", "description": "Q3 deliverables"},
            headers=headers,
        ).json()
        pid = project["id"]
        print(f"  project_id={pid}")

        # 4. Add tasks (single + bulk)
        print("\nAdding 3 tasks via bulk endpoint...")
        bulk = client.post(
            f"{API}/projects/{pid}/tasks/bulk",
            json={
                "tasks": [
                    {
                        "title": "Design auth flow",
                        "priority": "high",
                        "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                        "tags": ["design", "auth"],
                    },
                    {
                        "title": "Wire up CI",
                        "status": "in_progress",
                        "priority": "medium",
                    },
                    {
                        "title": "Write docs",
                        "status": "done",
                        "priority": "low",
                    },
                ]
            },
            headers=headers,
        ).json()
        print(f"  created {bulk['count']} tasks")

        # 5. List tasks
        print("\nAll tasks in project:")
        tasks = client.get(f"{API}/projects/{pid}/tasks", headers=headers).json()
        for t in tasks:
            tags = ",".join(tag["name"] for tag in t["tags"]) or "-"
            print(f"  [{t['status']:<11}] {t['priority']:<6} {t['title']:<25}  tags=[{tags}]")

        # 6. Get stats
        print("\nProject stats:")
        stats = client.get(f"{API}/projects/{pid}/stats", headers=headers).json()
        print(f"  total: {stats['total_tasks']}")
        print(f"  by_status: {stats['by_status']}")
        print(f"  by_priority: {stats['by_priority']}")
        print(f"  overdue: {stats['overdue']}")

        # 7. Export as CSV
        print("\nExporting CSV:")
        csv_resp = client.get(f"{API}/projects/{pid}/tasks/export", headers=headers)
        csv_path = f"sprint_{pid}_tasks.csv"
        with open(csv_path, "wb") as f:
            f.write(csv_resp.content)
        print(f"  saved to {csv_path} ({len(csv_resp.content)} bytes)")

        print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print(f"Could not reach {API}. Start the server first: uvicorn app.main:app --reload", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        sys.exit(1)
