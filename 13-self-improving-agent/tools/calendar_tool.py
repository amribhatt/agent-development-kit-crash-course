# tools/calendar_tool.py

def check_meeting_preferences(attendee_name: str) -> dict:
    """
    Simulates checking meeting preferences for a given attendee.
    In a real scenario, this would query a calendar or preferences database.
    """
    print(f"DEBUG: Simulating checking meeting preferences for {attendee_name}...")
    if attendee_name.lower() == "bob":
        return {"preferred_days": ["Tuesday", "Thursday"], "preferred_time_slot": "morning"}
    elif attendee_name.lower() == "alice":
        return {"preferred_days": ["Wednesday", "Friday"], "preferred_time_slot": "afternoon"}
    else:
        return {"preferred_days": ["any day"], "preferred_time_slot": "any time"}

def schedule_new_meeting(attendees: list[str], date: str, time: str, topic: str) -> str:
    """
    Simulates scheduling a new meeting.
    In a real scenario, this would interact with a calendar API (e.g., Google Calendar, Outlook).
    """
    print(f"DEBUG: Simulating scheduling meeting: Topic='{topic}', Date='{date}', Time='{time}', Attendees={attendees}")
    return f"Meeting '{topic}' scheduled for {date} at {time} with {', '.join(attendees)}. (Simulated)"
