import os
from functools import lru_cache

from agents import Agent, HostedMCPTool
from composio import Composio
from app.schemas.chat import AssistantResponse
from app.literals.system_prompts import SYSTEM_PROMPT_V2
from app.core.config import settings



def configure_openai() -> None:
    """Make the configured OpenAI API key available to the SDK."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured in backend settings"
        )

    os.environ["OPENAI_API_KEY"] = settings.openai_api_key


@lru_cache(maxsize=1)
def get_composio() -> Composio:
    if not settings.composio_api_key:
        raise RuntimeError("COMPOSIO_API_KEY is not configured")

    return Composio(api_key=settings.composio_api_key)


def create_agent(user_id: str) -> Agent:
    configure_openai()

    if not settings.model:
        raise RuntimeError("MODEL is not configured")

    session = get_composio().sessions.create(
        user_id=user_id,
        mcp=True,
    )

    mcp_tool = HostedMCPTool(
        tool_config={
            "type": "mcp",
            "server_label": "composio",
            "server_url": session.mcp.url,
            "headers": session.mcp.headers,
            "require_approval": settings.mcp_require_approval,
        }
    )

    return Agent(
        name="AuthSpaceAssistant",
        instructions=SYSTEM_PROMPT_V2,
        model=settings.model,
        tools=[mcp_tool],
        output_type=AssistantResponse,

    )
