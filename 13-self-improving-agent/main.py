# main.py
import asyncio
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

from google.adk.agents import Agent

from agents.email_triaging_agent import EmailTriagingAgent
from agents.email_writing_agent import EmailWritingAgent

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    print("DEBUG: google.generativeai configured with API key.")
else:
    print("ERROR: GOOGLE_API_KEY not found in environment after loading .env.")
    print("Please ensure your .env file is correctly set up in the same directory as main.py.")
    import sys
    sys.exit(1) # Exit if API key is not found, as LLM won't work


async def simulate_email_flow(email_content: str, sender_email: str, email_writer_agent: EmailWritingAgent):
    print(f"\n--- Incoming Email from: {sender_email} ---")
    print(f"Content:\n{email_content}")

    triage_agent = EmailTriagingAgent(name="simple_email_triage", model="simulated-basic")

    print("\n--- Triage Agent Processing ---")
    triage_result_json = await triage_agent.run(email_content, sender_email)
    triage_result = json.loads(triage_result_json)
    print(f"Triage Agent Decision: {json.dumps(triage_result, indent=2)}")

    if triage_result["ignore"]:
        print("\n--- Decision: Email ignored. No further action. ---")
    else:
        print("\n--- Decision: Responding to email. Passing to Writing Agent ---")

        current_action_type = triage_result.get("action_required", "draft response")
        initial_prompt_for_feedback = email_writer_agent._prompt_templates.get(current_action_type, "")

        drafted_email = await email_writer_agent.run(triage_result, sender_email)
        print("\n--- Drafted Email ---")
        print(drafted_email)

        # --- MODIFIED: Generic User Feedback ---
        feedback = input("\n[User Feedback]: Please provide any feedback for this email (or press Enter to skip improvement):\n> ").strip()
        if feedback: # Check if feedback string is not empty
            print("\n--- Initiating Prompt Improvement based on Feedback ---")
            await email_writer_agent.improve_prompt_template(
                action_type=current_action_type,
                previous_prompt=initial_prompt_for_feedback,
                generated_email=drafted_email,
                user_feedback=feedback
            )
            print("Prompt improvement process initiated. Check debug logs for new prompt.")
        else:
            print("No feedback provided. Prompt remains unchanged.")
        # --- END MODIFIED ---


async def main():
    print("Starting Email Assistance Demo (Writing Agent uses Gemini 1.5 Flash, env loaded from .env)...")

    email_writer_agent_instance = EmailWritingAgent(name="email_writer", model="gemini-1.5-flash")

    await simulate_email_flow(
        email_content="Hi team, could you please provide some information about the upcoming company picnic?",
        sender_email="alice@example.com",
        email_writer_agent=email_writer_agent_instance
    )

    await simulate_email_flow(
        email_content="Hello, I'd like to schedule a meeting with you to discuss the new project proposal. Are you free next week?",
        sender_email="bob@example.com",
        email_writer_agent=email_writer_agent_instance
    )

    await simulate_email_flow(
        email_content="Limited time offer! Buy now and get rich quick!!! SPAM SPAM SPAM",
        sender_email="scammer@badsite.com",
        email_writer_agent=email_writer_agent_instance
    )

    await simulate_email_flow(
        email_content="Thanks for the update! Appreciate it.",
        sender_email="charlie@example.com",
        email_writer_agent=email_writer_agent_instance
    )

    await simulate_email_flow(
        email_content="URGENT: Need your immediate feedback on the attached document. Action required by end of day!",
        sender_email="manager@example.com",
        email_writer_agent=email_writer_agent_instance
    )

    print("\nDemo Complete.")

if __name__ == "__main__":
    asyncio.run(main())