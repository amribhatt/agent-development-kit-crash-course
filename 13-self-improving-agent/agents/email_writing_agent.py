# agents/email_writing_agent.py
import json
from typing import Dict, Any
import os

from google.adk.agents import Agent
import google.generativeai as genai

PROMPT_TEMPLATES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prompt_templates.json')

class EmailWritingAgent(Agent):
    _llm_instance: genai.GenerativeModel | None = None
    _prompt_templates: Dict[str, str] = {}

    def __init__(self, name: str, model: str):
        super().__init__(name=name, model=model)
        if model.startswith("gemini-"):
            try:
                self._llm_instance = genai.GenerativeModel(model)
                print(f"DEBUG: EmailWritingAgent initialized with Gemini model: {model}")
            except Exception as e:
                print(f"ERROR: Failed to initialize Gemini model '{model}': {e}")
                self._llm_instance = None
        else:
            print(f"DEBUG: EmailWritingAgent initialized with non-Gemini model '{model}'. LLM calls will be skipped.")
            self._llm_instance = None

        self._load_prompt_templates()

    def _load_prompt_templates(self):
        if os.path.exists(PROMPT_TEMPLATES_FILE):
            with open(PROMPT_TEMPLATES_FILE, 'r') as f:
                self._prompt_templates = json.load(f)
            print(f"DEBUG: Loaded prompt templates from {PROMPT_TEMPLATES_FILE}")
        else:
            print(f"WARNING: Prompt templates file not found at {PROMPT_TEMPLATES_FILE}. Using default/empty templates.")
            self._prompt_templates = {
                "draft response": "You are an AI assistant tasked with writing polite and professional email responses. Your goal is to draft the BODY of an email (do NOT include the subject line). The original email was from: {sender_email}. Address the recipient as '{sender_name}'. Sign the email with 'EmailBot'. --- Instructions for Email Content Generation --- Based on the triage decision, the primary action required is: 'draft response'. The specific context or action to be performed is: '{response_summary}'. Draft a general polite response email to {sender_name}. Acknowledge their email and provide a brief, professional response that fulfills the purpose described by the summary. Do NOT use brackets or placeholders. Ensure the email is professional, concise, and friendly. Conclude with a standard closing.",
                "urgent action/response": "You are an AI assistant tasked with writing polite and professional email responses. Your goal is to draft the BODY of an email (do NOT include the subject line). The original email was from: {sender_email}. Address the recipient as '{sender_name}'. Sign the email with 'EmailBot'. --- Instructions for Email Content Generation --- Based on the triage decision, the primary action required is: 'urgent action/response'. The specific context or action to be performed is: '{response_summary}'. Draft an urgent email response to {sender_name}. Acknowledge the urgency and state that immediate action is being taken. Propose a next update by the next business day. Do NOT use brackets or placeholders. Ensure the email is professional, concise, and friendly. Conclude with a standard closing.",
                "schedule meeting": "You are an AI assistant tasked with writing polite and professional email responses. Your goal is to draft the BODY of an email (do NOT include the subject line). The original email was from: {sender_email}. Address the recipient as '{sender_name}'. Sign the email with 'EmailBot'. --- Instructions for Email Content Generation --- Based on the triage decision, the primary action required is: 'schedule meeting'. The specific context or action to be performed is: '{response_summary}'. The sender's preferred meeting details are: {meeting_details_json}. Draft an email to {sender_name} to follow up on their meeting request. Suggest a time like tomorrow, June 4th, at 10 AM BST, or ask for their general availability based on their preferences. Do NOT use brackets or placeholders. Ensure the email is professional, concise, and friendly. Conclude with a standard closing.",
                "provide information": "You are an AI assistant tasked with writing polite and professional email responses. Your goal is to draft the BODY of an email (do NOT include the subject line). The original email was from: {sender_email}. Address the recipient as '{sender_name}'. Sign the email with 'EmailBot'. --- Instructions for Email Content Generation --- Based on the triage decision, the primary action required is: 'provide information'. The specific context or action to be performed is: '{response_summary}'. Draft an email to {sender_name} to provide information. Acknowledge their question and directly provide the information as described by the summary. Do NOT use brackets or placeholders. Ensure the email is professional, concise, and friendly. Conclude with a standard closing."
            }


    def _save_prompt_templates(self):
        with open(PROMPT_TEMPLATES_FILE, 'w') as f:
            json.dump(self._prompt_templates, f, indent=4)
        print(f"DEBUG: Saved updated prompt templates to {PROMPT_TEMPLATES_FILE}")

    async def improve_prompt_template(self, action_type: str, previous_prompt: str, generated_email: str, user_feedback: str):
        if not self._llm_instance:
            print("ERROR: LLM not initialized. Cannot improve prompt without a model.")
            return

        # --- MODIFIED: Prompt for Improvement ---
        improvement_prompt = f"""
You are an AI assistant that helps refine instructions for another AI email writing agent.

Your goal is to adjust the prompt to better meet user expectations based on their feedback.

Here was the PREVIOUS PROMPT used to generate an email:
---
{previous_prompt}
---

Here was the EMAIL GENERATED by that prompt:
---
{generated_email}
---

Here is the USER FEEDBACK on the generated email:
---
{user_feedback}
---

Based on the user feedback, generate an IMPROVED PROMPT for the email writing agent for future emails of the type '{action_type}'.
The improved prompt should be a single, concise string, starting directly with the instructions.
It MUST retain placeholders for dynamic values like '{{sender_email}}', '{{sender_name}}', '{{response_summary}}', and '{{meeting_details_json}}' if applicable for the email type.
It MUST instruct the model to sign off as 'Amrita' and suggest 'next business day' for urgent responses.
It MUST explicitly instruct the model to NOT use any brackets or placeholders in its generated email.
Do NOT include any preamble, conversational text, or explanation in your response. Just provide the improved prompt string.
"""
        # --- END MODIFIED ---

        print(f"DEBUG: Sending improvement prompt to Gemini for '{action_type}'...")

        try:
            llm_response = self._llm_instance.generate_content(improvement_prompt)
            improved_prompt_text = llm_response.text.strip()

            if improved_prompt_text:
                self._prompt_templates[action_type] = improved_prompt_text
                self._save_prompt_templates()
                print(f"INFO: Prompt for '{action_type}' improved based on feedback.")
                print(f"New Prompt for '{action_type}':\n---\n{improved_prompt_text}\n---")
            else:
                print(f"WARNING: Gemini returned an empty improved prompt for '{action_type}'. No change made.")

        except Exception as e:
            print(f"ERROR: Failed to get improved prompt from Gemini for '{action_type}': {e}")


    async def run(self, triage_info: Dict[str, Any], sender_email: str) -> str:
        action_required = triage_info.get("action_required", "draft response")
        response_summary = triage_info.get("response_summary", "A general response is needed.")
        meeting_details = triage_info.get("meeting_details", {})

        sender_name = sender_email.split('@')[0].capitalize()

        drafted_email_subject = "Re: Your Email"

        base_prompt_template = self._prompt_templates.get(action_required, self._prompt_templates["draft response"])

        format_args = {
            "sender_email": sender_email,
            "sender_name": sender_name,
            "response_summary": response_summary,
            "meeting_details_json": json.dumps(meeting_details, indent=2) if meeting_details else "{}"
        }

        try:
            self.instruction = base_prompt_template.format(**format_args)
        except KeyError as e:
            print(f"ERROR: Missing placeholder in prompt template for '{action_required}': {e}. Using raw template.")
            self.instruction = base_prompt_template


        if action_required == "schedule meeting":
            drafted_email_subject = "Following up on your meeting request"
        elif action_required == "provide information":
            drafted_email_subject = "Regarding your question"
        elif action_required == "urgent action/response":
            drafted_email_subject = "URGENT: Regarding your email"

        print(f"DEBUG: Sending prompt to Gemini for {sender_email} (Action: {action_required})...")
        print(f"DEBUG: Prompt sent to Gemini:\n---\n{self.instruction}\n---")

        if self._llm_instance:
            try:
                llm_response = self._llm_instance.generate_content(self.instruction)
                email_body = llm_response.text
                print(f"DEBUG: Received response from Gemini for {sender_email}.")
            except Exception as e:
                print(f"ERROR: Failed to generate email with Gemini for {sender_email}: {e}")
                email_body = f"ERROR: Could not generate email due to LLM issue. Problem: {e}\n\nOriginal Action: {action_required}\nSummary: {response_summary}"
        else:
            email_body = f"DEBUG: Gemini model was not initialized. Please check your GOOGLE_API_KEY or Vertex AI setup in .env and main.py."
            email_body += f"\n\nSimulated response based on summary: {response_summary}"

        final_email = f"Subject: {drafted_email_subject}\n\n{email_body.strip()}"
        return final_email