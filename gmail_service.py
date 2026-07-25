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


def count_unread_emails(
    credential_data: dict[str, Any],
) -> int:
    """Return the number of unread inbox emails."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="in:inbox is:unread",
            maxResults=500,
        )
        .execute()
    )

    return int(result.get("resultSizeEstimate", 0))


def count_urgent_emails(
    credential_data: dict[str, Any],
) -> int:
    """Return unread emails marked important or starred."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="in:inbox is:unread {is:important is:starred}",
            maxResults=500,
        )
        .execute()
    )

    return int(result.get("resultSizeEstimate", 0))


def list_recent_emails(
    credential_data: dict[str, Any],
    max_results: int = 5,
) -> list[dict[str, str]]:
    """Return recent inbox email summaries."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="in:inbox",
            maxResults=max_results,
        )
        .execute()
    )

    emails: list[dict[str, str]] = []

    for item in result.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"],
            )
            .execute()
        )

        headers = {
            header["name"]: header["value"]
            for header in message.get("payload", {}).get("headers", [])
        }

        emails.append(
            {
                "subject": headers.get("Subject", "No subject"),
                "sender": headers.get("From", "Unknown sender"),
                "snippet": message.get("snippet", ""),
            }
        )

    return emails