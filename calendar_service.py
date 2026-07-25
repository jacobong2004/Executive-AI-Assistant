from __future__ import annotations

import os
import streamlit as st

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]

REDIRECT_URI = "https://vjqzqmwphtqbzenxu.streamlit.app"


def create_google_flow(state: str | None = None):
    """Create the Google web OAuth flow using Streamlit Secrets."""

    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": st.secrets["google_oauth"]["auth_uri"],
            "token_uri": st.secrets["google_oauth"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_oauth"][
                "auth_provider_x509_cert_url"
            ],
            "redirect_uris": [REDIRECT_URI],
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=False,
    )


def get_authorization_url() -> tuple[str, str]:
    """Generate the Google sign-in URL and security state."""
    flow = create_google_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return authorization_url, state


def exchange_code_for_credentials(
    code: str,
    expected_state: str,
) -> dict[str, Any]:
    """Exchange Google's returned code for user credentials."""
    flow = create_google_flow(state=expected_state)
    flow.fetch_token(code=code)

    credentials = flow.credentials

    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or SCOPES),
    }


def credentials_from_dict(data: dict[str, Any]) -> Credentials:
    """Rebuild Google credentials stored in the user's session."""
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )


def list_events(
    credential_data: dict[str, Any],
    max_results: int = 10,
) -> list[dict[str, str]]:
    """Return the signed-in user's upcoming calendar events."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    now = datetime.now(timezone.utc).isoformat()

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    formatted_events: list[dict[str, str]] = []

    for event in result.get("items", []):
        start_data = event.get("start", {})
        start = start_data.get("dateTime") or start_data.get("date", "")

        formatted_events.append(
            {
                "title": event.get("summary", "Untitled event"),
                "start": start,
                "location": event.get("location", ""),
            }
        )

    return formatted_events

def list_today_events(
    credential_data: dict[str, Any],
) -> list[dict[str, str]]:
    """Return today's events in Singapore time."""
    credentials = credentials_from_dict(credential_data)

    service = build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    singapore_time = ZoneInfo("Asia/Singapore")

    start_of_today = datetime.now(singapore_time).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    start_of_tomorrow = start_of_today + timedelta(days=1)

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_of_today.isoformat(),
            timeMax=start_of_tomorrow.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            timeZone="Asia/Singapore",
        )
        .execute()
    )

    formatted_events: list[dict[str, str]] = []

    for event in result.get("items", []):
        start_data = event.get("start", {})

        if "dateTime" in start_data:
            event_time = datetime.fromisoformat(
                start_data["dateTime"]
            ).astimezone(singapore_time)

            display_time = event_time.strftime("%-I:%M %p")
        else:
            display_time = "All day"

        formatted_events.append(
            {
                "title": event.get("summary", "Untitled event"),
                "start": display_time,
                "location": event.get("location", ""),
            }
        )

    return formatted_events