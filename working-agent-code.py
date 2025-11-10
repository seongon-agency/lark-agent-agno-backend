'''
Name: Content SEO AI Agents
Author: Hoang Duc Viet
Description: AI Agentic System for SEO content creation with Agno.
Version: 0.1.0
Latest changes: 
- connected to Arize Phoenix for tracing and evaluation.
- migrated to a different repo
NOTES:
- not being able to trace total token usage and costs due to agno itself.

TODO: 
- RAG

'''

from agno.agent import Agent
from agno.team import Team
from agno.os import AgentOS

# Model
from agno.models.anthropic import Claude
from agno.models.xai import xAI

# PostgreSQL Database (Supabase)
from agno.db.postgres import PostgresDb

# RAG Chromadb Database
# import chromadb
# from agno.knowledge.knowledge import Knowledge
# from agno.vectordb.chroma import ChromaDb
# from agno.knowledge.embedder.cohere import CohereEmbedder
# from chromadb.config import Settings
# import chromadb.utils.embedding_functions as embedding_functions


# Tools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.mcp import MultiMCPTools

# async run for MCP
import asyncio

# tracing and evaluation
from phoenix.otel import register

# Load environment variables
import os
import dotenv
dotenv.load_dotenv()

# Declare database

db = PostgresDb(
    db_url=os.getenv("SUPABASE_DB_URL"),
    # Table to store your Agent, Team and Workflow sessions and runs
    session_table="sessions",
    # Table to store all user memories
    memory_table="memory",
    # Table to store all metrics aggregations
    metrics_table="metrics",
    # Table to store all your evaluation data
    eval_table="evals",
    # Table to store all your knowledge content
    knowledge_table="knowledge",
)

# Configure RAG database with Chroma

## embedding with Cohere
# cohere_ef = embedding_functions.CohereEmbeddingFunction(
#     api_key=os.getenv('COHERE_API_KEY'),
#     model_name="embed-v4.0"
#     )

# client = chromadb.CloudClient(
#   api_key = "ck-5h8C36CwzBp81NwGoNjvZkNyrzEmjQcg5kkfPZVoQ8Pu",
#   tenant = 'de163e20-bb6f-4dc9-a7e8-51eab137d1ca',
#   database = 'agno'
# )

# knowledge = Knowledge(
#     name = "Story writing knowledge",
#     description = "Guidance on how to write effective short stories",
#     vector_db = ChromaDb(
#         collection="sample_collection",
#         embedder=CohereEmbedder(id="embed-v4.0", api_key="wiZKEho6gTFN97xutVtDKFp7pHIo7XDte10WXZfH"),
#         settings = Settings(
#             chroma_api_impl = "chromadb.api.fastapi.FastAPI",
#             chroma_server_host = "de163e20-bb6f-4dc9-a7e8-51eab137d1ca.api.trychroma.com",
#             chroma_server_http_port = 443,
#             chroma_server_ssl_enabled = True,
#             chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
#             chroma_client_auth_credentials="ck-5h8C36CwzBp81NwGoNjvZkNyrzEmjQcg5kkfPZVoQ8Pu"
#         )
#     )
# )



"""
SEO CONTENT CREATION TEAM

Members:
- Outline Agent
- Content Writer Agent
"""
# def content_team():
#     """Run AI Agent team."""
#     ## Declare MCP tools - Only Freepik (Mapbox removed due to timeout)
#     content_env = {
#             **os.environ,
#             'FREEPIK_API_KEY': os.getenv('FREEPIK_API_KEY'),
#     }

#     content_mcp_tools = MultiMCPTools(
#         commands=[
#             f"npx -y mcp-remote https://api.freepik.com/mcp --header x-freepik-api-key:{os.getenv('FREEPIK_API_KEY')}",
#         ],
#         env=content_env,
#         timeout_seconds=30,  # Increase timeout to 30 seconds
#         allow_partial_failure=True  # Allow agent to run even if Freepik connection fails
#     )

#     outline_agent = Agent(
#         name = "Outline Agent",
#         role = "Create a short story outline based on a given topic",
#         model = xAI(
#         id="grok-4-0709",
#         api_key=os.getenv("XAI_API_KEY"),
#         ),
#         description="You are short story idea creator. You generate an idea and suggest a clear outline base on a given topic",
#         instructions = [
#             "When asked to write a story, only return the story and nothing else.",
#             "Don't use icons and emojis"
#             ],
#         tools = [DuckDuckGoTools()],
#         # reasoning=True,
#         # reasoning_max_steps=10,
#         db = db,
#         add_history_to_context=True, ## retrieve conversaion history -> memory
#         read_chat_history=True, ## enables agent to read the chat history that were previously stored
#         # enable_session_summaries=True, ## summarizes the content of a long conversaion to storage
#         num_history_runs=2,
#         search_session_history=True, ## allow searching through past sessions
#         # num_history_sessions=2, ## retrieve only the 2 lastest sessions of the agent
#         markdown=True,
#         debug_mode=False,  # Hide intermediate output - only team sees this
#         cache_session=True
#     )

#     content_writer = Agent(
#         name = "Content Writer Agent",
#         role = "Write story based on a given outline",
#         model = xAI(
#         id="grok-4-0709",
#         api_key=os.getenv("XAI_API_KEY"),
#         ),
#         description="You are a short storywriter. Base on a given outline, you write a short compelling story.",
#         instructions=[
#             "Story must be under 500 words."
#             "When asked to write a story, only return the story text itself and nothing else.",
#             "DO NOT add images - another agent will handle that.",
#             "Never use emojis or icons."
#         ],
#         tools = [],
#         # reasoning=True,
#         # reasoning_max_steps=10,
#         db = db,
#         add_history_to_context=True, ## retrieve conversaion history -> memory
#         read_chat_history=True, ## enables agent to read the chat history that were previously stored
#         # enable_session_summaries=True, ## summarizes the content of a long conversaion to storage
#         num_history_runs=2,
#         search_session_history=True, ## allow searching through past sessions
#         # num_history_sessions=2, ## retrieve only the 2 lastest sessions of the agent
#         markdown=True,
#         debug_mode=False,  # Hide intermediate output - only team sees this
#         cache_session=True
#     )

#     image_integrator = Agent(
#         name = "Image Integration Agent",
#         role = "Insert relevant images into stories using Freepik",
#         model = xAI(
#         id="grok-4-0709",
#         api_key=os.getenv("XAI_API_KEY"),
#         ),
#         description="You are an image integration specialist. You analyze stories, identify key moments that need visual illustration, search for authentic real images using Freepik, and embed them into the story using markdown image syntax. You ONLY use real photography, never AI-generated images.",
#         instructions=[
#             "Analyze the story and identify 2-3 key moments or scenes that would benefit from images.",
#             "For each identified moment, use the search_resources tool from Freepik with ONLY the 'term' parameter.",
#             "Search using simple, descriptive terms like 'space rocket launch', 'ocean sunset', 'forest path'.",
#             "DO NOT use the 'filters' parameter - only use 'term' for searching.",
#             "From the search results, select images with high quality and relevance.",
#             "Use the download_resource_by_id tool to get the image URL for your selected images.",
#             "Insert images into the story using markdown syntax: ![description](image_url)",
#             "Place images strategically - typically after the paragraph that describes the scene.",
#             "Return the complete story with all images embedded in markdown format.",
#             "Never use emojis or icons."
#         ],
#         tools = [content_mcp_tools],
#         db = db,
#         add_history_to_context=True,
#         read_chat_history=True,
#         num_history_runs=2,
#         search_session_history=True,
#         markdown=True,
#         debug_mode=False,  # Hide intermediate output - only team sees this
#         cache_session=True
#     )

#     # content_evaluator = Agent(
#     #     name = "Content Evaluator Agent",
#     #     role = """
#     #         Evaluate a given story produced by a writer based on given criteria:
#     #         - Story must be under 500 words.
#     #         - Story must have the ending tied to the opening.
#     #         - Story must mention "Author: Viet" by the start of it.
#     #         """,
#     #     model = Claude(id="claude-sonnet-4-5-20250929", api_key=os.getenv("ANTHROPIC_API_KEY")),
#     #     description="You are a story reviewer. Base on a given story, you either approve or provide feedback",
#     #     instructions = [
#     #         "if the story is okay, only return 'approved'",
#     #         "if the story hasn't met the criteria, provide a short feedback checklist, each item clearly explaining what needs to be adjusted.",
#     #         "dont use any icons or emojies"
#     #     ],
#     #     db = db,
#     #     add_history_to_context=True, ## retrieve conversation history -> memory
#     #     read_chat_history=True, ## enables agent to read the chat history that were previously stored
#     #     # enable_session_summaries=True, ## summarizes the content of a long conversaion to storage
#     #     num_history_runs=2,
#     #     search_session_history=True, ## allow searching through past sessions
#     #     # num_history_sessions=2, ## retrieve only the 2 lastest sessions of the agent
#     #     markdown=True,
#     #     debug_mode=True,
#     #     cache_session=True
#     # )

#     content_team = Team(
#         name="AI SEO Content Team",
#         role="Coordinate the team members to create a short story with images. Every story MUST include images.",
#         model = xAI(
#         id="grok-4-0709",
#         api_key=os.getenv("XAI_API_KEY"),
#         ),
#         description="You coordinate a team to create illustrated short stories. Every story must have images embedded.",
#         instructions=[
#             "Step 1: Use outline agent to generate a story outline",
#             "Step 2: Use writer agent to produce the story text from the outline",
#             "Step 3: ALWAYS use image integration agent to add 2-3 relevant images to the story - this step is MANDATORY",
#             "Step 4: Verify that the final story has images embedded before returning it",
#             "Return ONLY the final story with images embedded in markdown format. DO NOT add extra words or explaining.",
#             "If the story doesn't have images, go back to step 3 and ensure the image integration agent adds them.",
#         ],
#         tools = [],
#         db = db,
#         # knowledge = knowledge,

#         add_history_to_context=True, ## retrieve conversaion history -> memory
#         read_team_history=True,
#         # enable_session_summaries=True, ## summarizes the content of a long conversaion to storage
#         num_history_runs=2,
#         search_session_history=True, ## allow searching through past sessions


#         # num_history_sessions=2, ## retrieve only the 2 lastest sessions of the agent
#         markdown=True,
#         debug_mode=True,
#         cache_session=True,


#         members=[outline_agent, content_writer, image_integrator],
#         # reasoning=True,
#         # reasoning_max_steps = 2,
#     )

#     agent_os = AgentOS(
#         id="my os",
#         description="My AgentOS",
#         # agents=[assistant],
#         teams=[content_team],
#         agents=[outline_agent, content_writer, image_integrator]
#     )

#     return agent_os


"""
LARK TASK AGENT
"""
"""
"lark-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@larksuiteoapi/lark-mcp",
        "mcp",
        "-a",
        "cli_a7e3876125b95010",
        "-s",
        "bnR0sCHHILwnt15g8Lr0HgTIbk0ZVelI",
        "-d",
        "https://open.larksuite.com/",
        "--oauth"
      ]
    },

"""
def lark_agent():
    """Run AI Agent team."""
    ## Declare MCP tools - Only Freepik (Mapbox removed due to timeout)
    content_env = {
            **os.environ,
            'FREEPIK_API_KEY': os.getenv('FREEPIK_API_KEY'),
    }

    lark_mcp = MultiMCPTools(
        commands=[
            # f"npx -y mcp-remote https://api.freepik.com/mcp --header x-freepik-api-key:{os.getenv('FREEPIK_API_KEY')}",
            f"npx -y @larksuiteoapi/lark-mcp mcp -a cli_a7e3876125b95010 -s bnR0sCHHILwnt15g8Lr0HgTIbk0ZVelI -d https://open.larksuite.com/ --oauth"
        ],
        # env=content_env,
        timeout_seconds=60,  # Increase timeout to 30 seconds
        allow_partial_failure=True  # Allow agent to run even if Freepik connection fails
    )

    lark_base_agent = Agent(
        name = "Lark Task Management Agent",
        role = "Manage Lark Tasks within a Lark Base using Lark MCP",
        model = xAI(
        id="grok-4-0709",
        api_key=os.getenv("XAI_API_KEY"),
        ),
        description="You are a task management assistant that helps users manage their tasks in Lark Base using Lark MCP. You can create, update, delete, and retrieve tasks based on user requests.",
        instructions=[
            "Use the Lark MCP tool to interact with Lark Base. The specific base id is 'Q9gVbS1j1anjh7sP56Dln1xFgdG'.",
            "When creating or updating tasks, ensure to include all necessary fields such as title, description, due date, and status.",
            "Always confirm actions with the user before making changes to their tasks.",
            "Provide clear and concise responses to the user regarding their task management requests."
        ],
        tools = [lark_mcp],
        db = db,
        add_history_to_context=True,
        read_chat_history=True,
        num_history_runs=2,
        search_session_history=True,
        markdown=True,
        debug_mode=False,  # Hide intermediate output - only team sees this
        cache_session=True
    )

    # content_team = Team(
    #     name="AI SEO Content Team",
    #     role="Coordinate the team members to create a short story with images. Every story MUST include images.",
    #     model = xAI(
    #     id="grok-4-0709",
    #     api_key=os.getenv("XAI_API_KEY"),
    #     ),
    #     description="You coordinate a team to create illustrated short stories. Every story must have images embedded.",
    #     instructions=[
    #         "Step 1: Use outline agent to generate a story outline",
    #         "Step 2: Use writer agent to produce the story text from the outline",
    #         "Step 3: ALWAYS use image integration agent to add 2-3 relevant images to the story - this step is MANDATORY",
    #         "Step 4: Verify that the final story has images embedded before returning it",
    #         "Return ONLY the final story with images embedded in markdown format. DO NOT add extra words or explaining.",
    #         "If the story doesn't have images, go back to step 3 and ensure the image integration agent adds them.",
    #     ],
    #     tools = [],
    #     db = db,
    #     # knowledge = knowledge,

    #     add_history_to_context=True, ## retrieve conversaion history -> memory
    #     read_team_history=True,
    #     # enable_session_summaries=True, ## summarizes the content of a long conversaion to storage
    #     num_history_runs=2,
    #     search_session_history=True, ## allow searching through past sessions


    #     # num_history_sessions=2, ## retrieve only the 2 lastest sessions of the agent
    #     markdown=True,
    #     debug_mode=True,
    #     cache_session=True,


    #     members=[outline_agent, content_writer, image_integrator],
    #     # reasoning=True,
    #     # reasoning_max_steps = 2,
    # )

    agent_os = AgentOS(
        id="my os",
        description="My AgentOS",
        # agents=[assistant],
        # teams=[content_team],
        agents=[lark_base_agent]
    )

    return agent_os


os_instance = lark_agent()
app = os_instance.get_app()

# Add CORS middleware to allow frontend to connect
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now - you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # Get port from environment variable (Railway) or default to 7778
    port = int(os.getenv("PORT", "7778"))
    host = os.getenv("HOST", "0.0.0.0")  # Listen on all interfaces for Docker/Railway

    os_instance.serve(
        app="agents:app",
        reload=False,
        port=port,
        host=host
    )
