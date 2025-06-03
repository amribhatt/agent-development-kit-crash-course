# agents/email_triaging_agent.py
import json
from typing import Dict, Any

from google.adk.agents import Agent

# Tool imports remain, though this simplified agent won't directly call them from here.
from tools.calendar_tool import check_meeting_preferences, schedule_new_meeting

class EmailTriagingAgent(Agent):
    """
    A very basic agent for triaging incoming emails.
    It uses simple rule-based logic to decide on actions.
    """
    def __init__(self, name: str, model: str):
        super().__init__(name=name, model=model)

    async def run(self, email_content: str, sender_email: str) -> str:
        email_lower = email_content.lower()

        triage_decision: Dict[str, Any] = {
            "ignore": False,
            "action_required": "draft response",
            "response_summary": "Requires a general response."
        }

        # --- Basic Triage Logic ---
        if "spam" in email_lower or "unsubscribing" in email_lower or "newsletter" in email_lower:
            triage_decision["ignore"] = True
            triage_decision["action_required"] = "ignore"
            triage_decision["response_summary"] = "Marked as spam/unimportant. No response needed."
        elif "thank you" in email_lower or "acknowledgement" in email_lower:
            triage_decision["ignore"] = True
            triage_decision["action_required"] = "ignore"
            triage_decision["response_summary"] = "Simple thank you email, no response needed."
        elif "meeting request" in email_lower or "schedule a call" in email_lower:
            triage_decision["ignore"] = False
            triage_decision["action_required"] = "schedule meeting"
            triage_decision["response_summary"] = f"Meeting request from {sender_email}. Needs scheduling."
            triage_decision["meeting_details"] = check_meeting_preferences(sender_email.split('@')[0].capitalize())
        elif "question about" in email_lower:
            triage_decision["ignore"] = False
            triage_decision["action_required"] = "provide information"
            triage_decision["response_summary"] = "Email asks a question. Needs information."
        elif "urgent" in email_lower or "action required" in email_lower:
            triage_decision["ignore"] = False
            triage_decision["action_required"] = "urgent action/response"
            # --- CHANGE MADE HERE ---
            # Make the summary a concise instruction for the writing agent.
            triage_decision["response_summary"] = "Address urgently and state that immediate steps are being taken."
            # --- END CHANGE ---
        # If none of the above, default is "draft response"

        print(f"DEBUG: Triage decision for {sender_email}: {triage_decision['action_required']}")
        return json.dumps(triage_decision)