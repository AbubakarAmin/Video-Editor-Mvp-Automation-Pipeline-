from google import genai
import os
import uuid
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types
from pydantic import BaseModel
#defining schema for api repsonse to get structred data in json

class video_in_json(BaseModel):
    start_time: str
    end_time: str
    visual: str


#function to genrate images using gemni image genration from visual decription json output 
# and retunr json with start_time,end_time and visual=path to image file
def generate_images_from_visuals(client,json_data, output_folder):
    print('Sending Visual Description TO api For Image genration')
    os.makedirs(output_folder, exist_ok=True)
    updated_json = []

    for scene in json_data:
        visual_description = scene.visual
        if not visual_description:
            continue

        try:
            # Request image generation from Gemini
            response = client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=visual_description,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    image = Image.open(BytesIO(image_data))
                    unique_name = f"scene_{uuid.uuid4().hex[:8]}.png"
                    image_path = os.path.join(output_folder, unique_name)
                    image.save(image_path)

                    # Replace the visual text with path to image
                    scene.visual = image_path
                    break

        except Exception as e:
            print(f"Failed to generate image for scene : {e}")
            continue

        updated_json.append(scene)

    return updated_json



def get_visual(api_key: str,audio_file_path: str,visual_output_path:str="Assets/Genrated_Visuals"):
    client = genai.Client(api_key=api_key)
    print("Sening Audio To api for visual Json")
    myfile = client.files.upload(file=audio_file_path)


    response = client.models.generate_content(
            model="gemini-2.5-flash", contents = ["""
    You are a world-class cinematic director and visual storyteller. Your task is to convert the following audio script into a series of vivid, well-described visual scenes that will be used to generate images using an AI image generation model. 

    Generate a structure that divides the script into time-based segments, and for each segment, provide a **highly descriptive, realistic, and coherent scene**. The visual descriptions must:

    - Be richly detailed (enough to generate high-quality images).
    - Reflect continuity between scenes (as if part of the same cinematic video).
    - Capture the tone and emotion conveyed in the audio (e.g., peaceful, intense, nostalgic).
    - Be grounded in reality (avoid fantasy or surrealism unless clearly implied).
    - Be camera-aware: use phrases like “wide aerial shot,” “close-up of,” “camera slowly pans over,” “over-the-shoulder view, and more that you think are good” etc.

    These visuals will be used to generate AI images **frame-by-frame** and stitched into a cohesive video, so **maintaining visual and thematic continuity** is essential again maintaining continuity is must.
    """,myfile]
    ,
    config={
            "response_mime_type": "application/json",
            "response_schema": list[video_in_json],
        },

        )
    print("Recieved Visual Json from API")
    visual_json: list[video_in_json] = response.parsed

    return generate_images_from_visuals(client,visual_json,visual_output_path)
    