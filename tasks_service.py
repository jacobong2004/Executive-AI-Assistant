from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def credentials_from_dict(
    credential_data: dict[str, Any],
) -> Credentials:
    """Rebuild Google credentials from Streamlit session data."""
    return Credentials(
        token=credential_data.get("token"),
        refresh_token=credential_data.get("refresh_token"),
        token_uri=credential_data.get("token_uri"),
        client_id=credential_data.get("client_id"),
        client_secret=credential_data.get("client_secret"),
        scopes=credential_data.get("scopes"),
    )


def count_completed_tasks(
    credential_data: dict[str, Any],
) -> int:
    """Count completed tasks across the user's task lists."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "tasks",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    tasklists_result = service.tasklists().list(maxResults=100).execute()

    completed_count = 0

    for tasklist in tasklists_result.get("items", []):
        tasks_result = (
            service.tasks()
            .list(
                tasklist=tasklist["id"],
                showCompleted=True,
                showHidden=True,
                maxResults=100,
            )
            .execute()
        )

        for task in tasks_result.get("items", []):
            if task.get("status") == "completed":
                completed_count += 1

    return completed_count


def list_pending_tasks(
    credential_data: dict[str, Any],
    max_results: int = 5,
) -> list[dict[str, str]]:
    """Return pending tasks from the user's task lists."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "tasks",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    tasklists_result = service.tasklists().list(maxResults=100).execute()

    pending_tasks: list[dict[str, str]] = []

    for tasklist in tasklists_result.get("items", []):
        tasks_result = (
            service.tasks()
            .list(
                tasklist=tasklist["id"],
                showCompleted=False,
                maxResults=max_results,
            )
            .execute()
        )

        for task in tasks_result.get("items", []):
            pending_tasks.append(
                {
                    "title": task.get("title", "Untitled task"),
                    "due": task.get("due", ""),
                    "tasklist": tasklist.get("title", "Tasks"),
                }
            )

            if len(pending_tasks) >= max_results:
                return pending_tasks

    return pending_tasks