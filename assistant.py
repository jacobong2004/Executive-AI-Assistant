import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY was not found. Check that your local .env file exists."
    )

client = OpenAI(api_key=api_key)


def ask_assistant(
    messages: list[dict[str, str]],
    account_context: str = "",
) -> str:
    """Answer the user using conversation history and live account data."""

    if not messages:
        return "Please enter a question."

    instructions = """
You are a professional Executive AI Assistant.

Help the user:
- understand and prioritise emails
- prepare for meetings
- review calendar events
- manage pending tasks
- draft professional messages
- decide what requires attention first

Use the live account context provided below when answering.

Important rules:
- Never invent emails, meetings, tasks, dates, names, or details.
- If information is not available in the context, clearly say so.
- Do not claim an action has been completed unless the app confirms it.
- For actions such as sending emails, creating tasks, or scheduling meetings,
  prepare a draft and request approval first.
- Keep responses practical, professional, and easy to scan.

LIVE ACCOUNT CONTEXT:
""" + (account_context or "No live Google account information was provided.")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=instructions,
            input=messages,
        )

        return response.output_text

    except Exception as error:
        return f"Unable to contact the AI service: {error}"