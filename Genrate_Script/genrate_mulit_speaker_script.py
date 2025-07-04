from google import genai
from pydantic import BaseModel
#defining schema for api repsonse to get structred data in json

class script_in_json(BaseModel):
    script:str
    tone:str
   


def genrate_multi_speaker_script(api_key:str,audience:str,topic:str):
 
     client = genai.Client(api_key=api_key)
     print("Writing Script........")
     response = client.models.generate_content(
     model="gemini-2.5-flash", contents = [f"""
    Write a video script designed to instantly hook viewers within the first 5 seconds, using either an emotional, shocking, or curiosity-driven opening line.
Use two speakers: Speaker1: (female voice) and Speaker2: (male voice). Alternate between them naturally to create engaging, human-like conversation.
This script will be used in a text-to-speech (TTS) pipeline, so include emotional cues, sound effects, and actions in parentheses — e.g., (laughs), (gasps), (typing sounds), (dramatic pause), etc.
The conversation should feel  real — include natural pauses, banter, reactions, and scene-setting details.
Make sure the script builds suspense or emotion, delivers valuable or surprising information, and ends with a punch or emotional payoff.
Avoid fluff or filler. Hook fast, then flow smoothly.

Target audience: {audience}

Topic: {topic}

Output format: Use plain text with Speaker1: and Speaker2: tags only — no narration or stage directions outside of parentheses.
tone: [e.g., cinematic + dramatic, or conversational + humorous + mysterious — combine as needed]. you can also defien your tone in detail and as combination of many as required to you

No extra explanation or intro — just the script.
    """]
     ,
     config={
            "response_mime_type": "application/json",
            "response_schema": script_in_json,
        },)
     script_json:script_in_json = response.parsed
     return (f"{script_json.tone}:{script_json.script}")
