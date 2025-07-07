import os
import uuid
import requests
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class video_in_json(BaseModel):
    start_time: str
    end_time: str
    search_tags_on_pixels: str  # We now expect this to be short search phrases

def download_videos_from_pexels(visual_json,orientation, output_folder):
    print("Downloading stock videos from Pexels...")
    os.makedirs(output_folder, exist_ok=True)
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    updated_json = []
    

    for scene in visual_json:
        query = scene.search_tags_on_pixels
        if not query:
            continue

        try:
            response = requests.get(
                "https://api.pexels.com/videos/search",
                params={"query": query, "orientation":orientation,"per_page": 1},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("videos"):
                video_url = data["videos"][0]["video_files"][0]["link"]
                file_ext = video_url.split('.')[-1]
                file_name = f"scene_{uuid.uuid4().hex[:8]}.{file_ext}"
                file_path = os.path.join(output_folder, file_name)

                video_data = requests.get(video_url).content
                with open(file_path, "wb") as f:
                    f.write(video_data)

                scene.search_tags_on_pixels = file_path
                updated_json.append(scene)
            else:
                print(f"No video found for query: {query}")

        except Exception as e:
            print(f"Failed to fetch video for query '{query}': {e}")

    return updated_json

def get_visual(api_key: str, audio_file_path: str,orientation:str, visual_output_path: str = "Assets/Downloaded_Clips"):
    client = genai.Client(api_key=api_key)
    print("Sending Audio To API for Visual Tags...")
    myfile = client.files.upload(file=audio_file_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
            """
            You are a cinematic director. Your task is to break this audio script into visual scenes.

            For each segment, return:
            - start_time
            - end_time
            - search_tags_on_pixels: a **short, relevant keyword or phrase** describing the scene to help search for real-world video stock on sites like Pexels. 
              Example: "sunset over mountains", "people walking on street", "closeup of crying woman".

            Avoid full sentences. Only return brief search tags.
            Keep video fast paced.
            You **Must** match the length of audio in your timestamps.
            Visuals **MUST** be in sync with audio
            Return a structured JSON list.
            """,
            myfile
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[video_in_json],
        },
    )
    print("Received Visual Tags from API")
    visual_json: list[video_in_json] = response.parsed

    return download_videos_from_pexels(visual_json, orientation,visual_output_path)
