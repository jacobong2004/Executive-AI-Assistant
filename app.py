from datetime import datetime

import streamlit as st

from memory_service import load_memory, save_memory

from memory_service import clear_memory

if st.sidebar.button("🗑️ Clear Chat"):
    clear_memory()
    st.session_state.messages = []
    st.rerun()

from assistant import ask_assistant
from calendar_service import (
    exchange_code_for_credentials,
    get_authorization_url,
    list_events,
    list_today_events,
)

from gmail_service import (
    count_unread_emails,
    count_urgent_emails,
    list_recent_emails,
)

from tasks_service import (
    count_completed_tasks,
    list_pending_tasks,
)

st.set_page_config(
    page_title="Executive AI Assistant",
    page_icon="🤖",
    layout="wide",
)


def initialise_state() -> None:
    if "approval_status" not in st.session_state:
        st.session_state.approval_status = "Pending"

    if "messages" not in st.session_state:
        saved_memory = load_memory()
        st.session_state.messages = saved_memory.get("messages", [])

    if "google_credentials" not in st.session_state:
        st.session_state.google_credentials = None

    if "oauth_state" not in st.session_state:
        st.session_state.oauth_state = None
       
def process_google_callback() -> None:
    params = st.query_params

    if "code" not in params:
        return

    if "state" not in params:
        st.error("Google did not return the OAuth state.")
        return

    try:
        credentials = exchange_code_for_credentials(
            params["code"],
            params["state"],
        )

        st.session_state.google_credentials = credentials
        st.query_params.clear()

        st.success("Google Calendar connected successfully.")

    except Exception as error:
        st.error(f"Google connection failed: {error}")

def display_sidebar() -> None:
    """Display the application's navigation sidebar."""
    with st.sidebar:
        st.title("🤖 Executive AI")
        st.caption("Your intelligent command centre")

        st.info("📅 Google Calendar is temporarily disabled.")       

        st.divider()

        if st.session_state.google_credentials is None:
            auth_url, state = get_authorization_url()
            st.session_state.oauth_state = state

            st.link_button(
                "🔗 Connect Google Calendar",
                auth_url,
                use_container_width=True,
            )
else:
    st.success("✅ Google Calendar Connected")

        st.button("🏠 Dashboard", use_container_width=True)
        st.button("📧 Emails", use_container_width=True)
        st.button("📅 Calendar", use_container_width=True)
        st.button("✅ Approvals", use_container_width=True)

        st.divider()
        st.caption("Prototype version 1.0")


def display_metrics() -> None:
    """Display live executive summary cards."""
    email_column, meeting_column, urgent_column, task_column = st.columns(4)

    unread_count: int | str = "—"
    meeting_count: int | str = "—"
    urgent_count: int | str = "—"
    completed_count: int | str = "—"

    next_meeting = "Connect Google"
    email_caption = "Connect Google"
    urgent_caption = "Connect Google"
    task_caption = "Connect Google"

    credentials = st.session_state.google_credentials

    if credentials is not None:
        try:
            events = list_events(credentials, max_results=10)
            meeting_count = len(events)

            if events:
                next_meeting = f"Next: {events[0].get('start', 'Time unavailable')}"
            else:
                next_meeting = "No upcoming meetings"
        except Exception:
            next_meeting = "Calendar unavailable"

        try:
            unread_count = count_unread_emails(credentials)
            email_caption = "Unread inbox emails"
        except Exception:
            email_caption = "Gmail unavailable"

        try:
            urgent_count = count_urgent_emails(credentials)
            urgent_caption = "Unread important emails"
        except Exception:
            urgent_caption = "Gmail unavailable"

        try:
            completed_count = count_completed_tasks(credentials)
            task_caption = "Completed Google Tasks"
        except Exception:
            task_caption = "Tasks unavailable"

    with email_column:
        st.metric(
            "Unread emails",
            unread_count,
            email_caption,
        )

    with meeting_column:
        st.metric(
            "Upcoming meetings",
            meeting_count,
            next_meeting,
        )

    with urgent_column:
        st.metric(
            "Urgent items",
            urgent_count,
            urgent_caption,
        )

    with task_column:
        st.metric(
            "Completed tasks",
            completed_count,
            task_caption,
        )


def display_briefing() -> None:
    """Display a briefing based on available account connections."""
    st.subheader("✨ AI Executive Briefing")

    if st.session_state.google_credentials is None:
        st.info(
            "Connect Google Calendar to generate your live executive briefing."
        )
        return

    try:
        events = list_events(
            st.session_state.google_credentials,
            max_results=5,
        )

        if not events:
            st.success(
                "You currently have no upcoming calendar events."
            )
            return

        briefing_lines = [
            "**Here are your upcoming priorities:**",
            "",
        ]

        for index, event in enumerate(events, start=1):
            title = event.get("title", "Untitled event")
            start = event.get("start", "Time unavailable")

            briefing_lines.append(
                f"{index}. **{title}** — {start}"
            )

        st.info("\n".join(briefing_lines))

    except Exception as error:
        st.error(f"Unable to generate briefing: {error}")

def build_account_context() -> str:
    """Create a safe text summary of the user's live Google data."""
    credentials = st.session_state.google_credentials

    if credentials is None:
        return "Google is not connected."

    context_sections = []

    # Recent emails
    try:
        emails = list_recent_emails(credentials, max_results=10)

        if emails:
            email_lines = ["RECENT EMAILS:"]

            for email in emails:
                email_lines.append(
                    f"- Subject: {email.get('subject', 'No subject')}\n"
                    f"  Sender: {email.get('sender', 'Unknown sender')}\n"
                    f"  Preview: {email.get('snippet', 'No preview')}"
                )

            context_sections.append("\n".join(email_lines))
        else:
            context_sections.append("RECENT EMAILS:\n- No recent emails found.")

    except Exception as error:
        context_sections.append(
            f"RECENT EMAILS:\n- Unable to retrieve emails: {error}"
        )

    # Upcoming calendar events
    try:
        events = list_events(credentials, max_results=10)

        if events:
            event_lines = ["UPCOMING CALENDAR EVENTS:"]

            for event in events:
                title = event.get("summary", event.get("title", "Untitled event"))
                start = event.get("start", "Start time unavailable")

                event_lines.append(f"- {title} — {start}")

            context_sections.append("\n".join(event_lines))
        else:
            context_sections.append(
                "UPCOMING CALENDAR EVENTS:\n- No upcoming events found."
            )

    except Exception as error:
        context_sections.append(
            f"UPCOMING CALENDAR EVENTS:\n- Unable to retrieve events: {error}"
        )

    # Pending Google Tasks
    try:
        tasks = list_pending_tasks(credentials)

        if tasks:
            task_lines = ["PENDING TASKS:"]

            for task in tasks:
                title = task.get("title", "Untitled task")
                due = task.get("due", "No due date")

                task_lines.append(f"- {title} — Due: {due}")

            context_sections.append("\n".join(task_lines))
        else:
            context_sections.append("PENDING TASKS:\n- No pending tasks found.")

    except Exception as error:
        context_sections.append(
            f"PENDING TASKS:\n- Unable to retrieve tasks: {error}"
        )

    return "\n\n".join(context_sections)

def build_account_context() -> str:
    """Build a live summary of the connected Google account."""

    if st.session_state.google_credentials is None:
        return "Google account is not connected."

    context = []

    try:
        unread = count_unread_emails(st.session_state.google_credentials)
        urgent = count_urgent_emails(st.session_state.google_credentials)

        context.append(f"Unread emails: {unread}")
        context.append(f"Urgent emails: {urgent}")
    except Exception:
        pass

    try:
        tasks = list_pending_tasks(st.session_state.google_credentials)

        if tasks:
            context.append("Pending tasks:")
            for task in tasks[:5]:
                context.append(f"- {task}")
    except Exception:
        pass

    try:
        events = list_events(
            st.session_state.google_credentials,
            max_results=5,
        )

        if events:
            context.append("Upcoming meetings:")
            for event in events:
                context.append(
                    f"- {event['summary']} at {event['start']}"
                )
    except Exception:
        pass

    return "\n".join(context)


def display_chat() -> None:
    """Display the AI-powered chat interface."""

    st.subheader("💬 Ask your assistant")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input(
        "Ask about emails, meetings, priorities or pending work..."
    )

    if user_question:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_question,
            }
        )

        with st.chat_message("user"):
            st.write(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                account_context = build_account_context()

                response = ask_assistant(
                    st.session_state.messages,
                    account_context=account_context,
                )

            st.write(response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )
        save_memory(
    {
        "messages": st.session_state.messages,
        "user_preferences": {},
    }
)


def display_schedule() -> None:
    """Display the signed-in user's upcoming Google Calendar events."""
    st.subheader("📅 Upcoming Schedule")

    if st.session_state.google_credentials is None:
        st.info("Connect Google Calendar to view your real events.")
        return

    try:
        events = list_today_events(
    st.session_state.google_credentials,
)

        if not events:
            st.info("No upcoming calendar events found.")
            return

        for event in events:
            title = event.get("title", "Untitled event")
            start = event.get("start", "")
            location = event.get("location", "")

            st.write(f"**{start}** — {title}")

            if location:
                st.caption(f"📍 {location}")

    except Exception as error:
        st.error(f"Unable to load Calendar events: {error}")


def display_approval() -> None:
    """Display pending assistant actions."""
    st.subheader("✅ Pending Approval")
    st.info("No pending approvals.")

    approve_column, reject_column = st.columns(2)

    with approve_column:
        if st.button(
            "Approve draft",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.approval_status = "Approved"

    with reject_column:
        if st.button(
            "Reject draft",
            use_container_width=True,
        ):
            st.session_state.approval_status = "Rejected"

    status = st.session_state.approval_status

    if status == "Approved":
        st.success("Draft approved. No real email was sent.")
    elif status == "Rejected":
        st.error("Draft rejected.")
    else:
        st.caption("Status: Pending approval")

def display_work_overview() -> None:
    """Display recent emails and pending Google Tasks."""
    credentials = st.session_state.google_credentials

    if credentials is None:
        st.info("Connect Google to view emails and tasks.")
        return

    email_column, task_column = st.columns(2)

    with email_column:
        st.subheader("📧 Recent Emails")

        try:
            emails = list_recent_emails(credentials, max_results=5)

            if not emails:
                st.info("No recent inbox emails.")
            else:
                for email in emails:
                    st.write(f"**{email['subject']}**")
                    st.caption(email["sender"])
                    st.write(email["snippet"])
                    st.divider()

        except Exception as error:
            st.error(f"Unable to load Gmail: {error}")

    with task_column:
        st.subheader("✅ Pending Tasks")

        try:
            tasks = list_pending_tasks(credentials, max_results=5)

            if not tasks:
                st.success("No pending Google Tasks.")
            else:
                for task in tasks:
                    st.write(f"**{task['title']}**")

                    if task["due"]:
                        st.caption(f"Due: {task['due']}")
                    else:
                        st.caption(task["tasklist"])

                    st.divider()

        except Exception as error:
            st.error(f"Unable to load Tasks: {error}")

def main() -> None:
    initialise_state()
    process_google_callback()
    display_sidebar()

    st.title("Executive AI Assistant")

    st.divider()
    display_metrics()
    st.divider()

    display_work_overview()

    st.divider()

    main_column, side_column = st.columns([2, 1])

    with main_column:
        display_briefing()
        display_chat()

    with side_column:
        display_schedule()
        st.divider()
        display_approval()


if __name__ == "__main__":
    main()