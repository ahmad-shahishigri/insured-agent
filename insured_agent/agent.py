import sys
from pathlib import Path
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

PROJECT_DIR = Path(__file__).parent
MCP_SERVER_PATH = PROJECT_DIR / "server.py"

root_agent = Agent(
    name="insurance_agent",
    model="gemini-2.0-flash",
    description="Insurance assistant with access to NowCerts insured list and insert capabilities.",
    instruction="""
You are a helpful insurance assistant.
Use get_insured_list when user asks for insured records.
Use insert_insured when user wants to add a new insured record.
Summarize clearly and confirm actions before proceeding.
""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[str(MCP_SERVER_PATH)],
                    cwd=str(PROJECT_DIR),
                ),
                timeout=20.0,  # allow longer time for tool responses
            ),
        )
    ],
)
