from google import genai
from pydantic import BaseModel

class video_in_json(BaseModel):
    start_time: str
    end_time: str
    visual: str

def get_visual(api_key: str,audio_file_path: str):
    client = genai.Client(api_key=api_key)
    print
    myfile = client.files.upload(file=audio_file_path)


    response = client.models.generate_content(
        model="gemini-2.5-flash", contents = ["""
You are a world-class cinematic director and visual storyteller. Your task is to convert the following audio script into a series of vivid, well-described visual scenes that will be used to generate images using an AI image generation model. 

Generate a structure that divides the script into time-based segments, and for each segment, provide a **highly descriptive, realistic, and coherent scene**. The visual descriptions must:

- Be richly detailed (enough to generate high-quality images).
- Reflect continuity between scenes (as if part of the same cinematic video).
- Capture the tone and emotion conveyed in the audio (e.g., peaceful, intense, nostalgic).
- Be grounded in reality (avoid fantasy or surrealism unless clearly implied).
- Be camera-aware: use phrases like “wide aerial shot,” “close-up of,” “camera slowly pans over,” “over-the-shoulder view,” etc.

These visuals will be used to generate AI images **frame-by-frame** and stitched into a cohesive video, so **maintaining visual and thematic continuity** is essential.
"""]
,
config={
        "response_mime_type": "application/json",
        "response_schema": list[video_in_json],
    },

    )

    return response.text