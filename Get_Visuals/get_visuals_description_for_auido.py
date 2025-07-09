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
    search_tags_on_pexels: str
    search_tag_for_sfx_from_freesound:str  # We now expect this to be short search phrases

import os
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_video(scene, headers, orientation, output_folder):
    query = scene.search_tags_on_pexels
    if not query:
        return None

    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            params={"query": query, "orientation": orientation, "per_page": 1},
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

            video_response = requests.get(video_url, stream=True, timeout=20)
            video_response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in video_response.iter_content(chunk_size=1048576):
                    if chunk:
                        f.write(chunk)

            scene.search_tags_on_pexels = file_path
            return scene
        else:
            print(f"No video found for query: {query}")
            return None

    except Exception as e:
        print(f"Failed to fetch video for query '{query}': {e}")
        return None


def download_videos_from_pexels(visual_json, orientation, output_folder, max_workers=5):
    print("Downloading stock videos from Pexels...")
    os.makedirs(output_folder, exist_ok=True)
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    updated_json = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_video, scene, headers, orientation, output_folder)
            for scene in visual_json if scene.search_tags_on_pexels
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                updated_json.append(result)

    return updated_json

def get_visual(api_key: str, audio_file_path: str,orientation:str, visual_output_path: str = "Assets/Downloaded_Clips"):
    client = genai.Client(api_key=api_key)
    print("Sending Audio To API for Visual Tags...")
    myfile = client.files.upload(file=audio_file_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[
           """ You are a cinematic video director and editor. Your task is to break this voiceover/audio script into tightly synced visual scenes **and** matching sound effects.

🔹 Your response must be a JSON list. Each item in the list should contain:
- "start_time": when this scene starts (format: "00:00")
- "end_time": when this scene ends (format: "00:00")
- "search_tags_on_pexels": a **short, cinematic, and emotionally resonant keyword or phrase** to search for relevant video clips (e.g. on Pexels).
- "search_tag_for_sfx_on_pixabay": a **brief, realistic sound effect keyword** to search for cinematic SFX on Pixabay.  
  ⚠️ If a scene does **not** require sound effects, leave this field as an **empty string** like this `""`.

---

🔹 Guidelines for `search_tags_on_pexels`:

- DO NOT write full sentences. Use **short, specific, visual phrases only**.
- Choose clips that are **cinematic, not generic** — prefer **emotionally rich, visually striking, or symbolic** shots.
- Use keywords that imply **composition** or **camera movement** if needed: e.g. `"slow motion punch"`, `"aerial view of forest"`, `"closeup of crying woman"`.
- Match the **emotional tone and energy** of the audio: sadness, awe, intensity, suspense, chaos, hope, etc.
- Capture **metaphor or mood**, not just literal meaning. E.g., for "loss" you can use: `"empty chair"`, `"sunset over graveyard"`, `"old man looking out window"`.

---

🔹 Guidelines for `search_tag_for_sfx_on_pixabay`:

- Provide **only one sound keyword** per scene.
- Tag must be **short** — ideally **1 word**, maximum **2 words**.
- DO NOT combine multiple sounds like `"rain, thunder"` — pick the **strongest or most relevant**.
- If no sound is needed, return an empty string: `""`.

✅ Good: `"thunder"`, `"typing"`, `"explosion"`, `"heartbeat"`, `"crackling"`  
❌ Bad: `"rain and thunder"`, `"soft piano in distance"`, `"crowd clapping and cheering"`

---

🔹 Examples of `search_tags_on_pexels`:
- "sunset over mountains"
- "closeup of crying woman"
- "people walking on street"
- "car speeding on highway"
- "man staring at horizon"
- "city lights at night"
- "battlefield explosion"
- "student raising hand in class"
- "hands typing on laptop"
- "stormy ocean waves"
- "child running through field"
- "robot assembling in factory"
- "old man sitting alone"
- "hacker typing in dark room"
- "mother hugging child"
- "spacecraft launching into sky"
- "fireworks in night sky"
- "athlete crossing finish line"
- "drone flying over desert"
- "closeup of teardrop"
- "broken mirror on floor"
- "girl smiling through tears"
- "lone figure walking in fog"
- "silhouette against sunrise"
- "hand letting go of balloon"
- "angry man yelling in rain"
- "books falling from shelf"
- "zoom into eye"
- "paper burning slowly"

---

🔹 Examples of `search_tag_for_sfx_on_pixabay`:
"footsteps", "gunshot", "thunder", "rain", "typing", "explosion", "heartbeat",  
"swoosh", "applause", "clapping", "door", "creak", "birds", "wind", "fire", "crackling",  
"scream", "laugh", "alarm", "engine", "siren", "whisper", "whoosh", "bark", "meow",  
"growl", "glass", "splash", "drone", "sword", "clang", "beep", "ambient", "forest",  
"piano", "strings", "clock", "riser", "flicker", "shutter", "roar", "echo", "bell",  
"shot", "rumble", "buzz", "zap", "sizzle", "march", "train", "breathe", "click",  
"strike", "boom", "drums", "chant", "tap"

---

🎬 **Be cinematic, rhythmic, and immersive.** Your goal is to produce video cues and SFX that feel like a **professionally edited trailer or short film**, using emotionally resonant visuals and immersive sound design to amplify the storytelling.
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
