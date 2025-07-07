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
  You are a world-class scriptwriter. Write a **highly engaging two-speaker video script** optimized for social media.

### Instructions:
- **Hook** viewers in the **first 5 seconds** using either:
  - a shocking fact,
  - a powerful emotional statement, or
  - an irresistible curiosity gap.
- Use **two speakers**:
  - Speaker1: (female voice)
  - Speaker2: (male voice)
- Alternate speakers naturally to simulate real, human-like **dialogue**.
- The script will be **converted to TTS**, so include emotional cues. Examples:
  - (laughs), (gasps),(dramatic pause),
- Prioritize **emotional arcs**, **storytelling**, and **valuable or surprising information**.
- The **ending must deliver a punchline, twist, or emotional resolution**.
- Avoid fluff or generic statements — make every line **count**.

### Target Audience:
{audience}

### Topic:
{topic}

### Tone:
Combine multiple styles as needed (e.g., cinematic + mysterious, or humorous + intense). Describe and adapt tone based on what best suits the topic and audience.

### Format:
- Output as plain text.
- Use `Speaker1:` and `Speaker2:` tags only.
- No narration or stage directions .
-and also specify tone in which this whole script should be read.
    """]
     ,
     config={
            "response_mime_type": "application/json",
            "response_schema": script_in_json,
        },)
     script_json:script_in_json = response.parsed
     return (f"{script_json.tone}:{script_json.script}")
