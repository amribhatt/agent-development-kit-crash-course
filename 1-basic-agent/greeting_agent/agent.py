from google.adk.agents import Agent

root_agent = Agent(
    name="greeting_agent",
    # https://ai.google.dev/gemini-api/docs/models
    # original model="gemini-2.0-flash"
    model="gemini-2.5-flash-preview-05-20",
    description="Greeting agent",
    instruction="""
    You are a helpful assistant that greets the user. 
    Ask for the user's name and greet them by name.
    """,
)
