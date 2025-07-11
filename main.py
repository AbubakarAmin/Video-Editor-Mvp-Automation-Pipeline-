from Genrate_Script.genrate_mulit_speaker_script import genrate_multi_speaker_script
from TTS.genrate_audio import generate_and_save_multi_speaker_audio
from Get_Visuals.get_visuals_description_for_auido import get_visual
from SFX.get_sfx_from_freesound import process_sfx_json_and_download
from Edit_Final_Video.edit_final_video import create_video_from_video_clips_and_audio
from dotenv import load_dotenv
import os
load_dotenv()
import sentry_sdk

sentry_sdk.init(
    dsn="https://7e15686187d622830eb6fc4abb2a4a38@o4509650995249152.ingest.de.sentry.io/4509651006062672",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)
division_by_zero = 1 / 0
api_key=os.getenv("GEMINI_API_KEY") 
audience=input("Target Audience: ")
topic=input("Enter your topic : ")
orientation=input("orientation(landscape=1,potrait=2,square=3):  ")
orientation= (
    "landscape" if orientation == '1' else
    "square" if orientation== '3' else
    'portrait'
)


script =genrate_multi_speaker_script(api_key=api_key,audience=audience,topic=topic) 

    # Call the function to generate and save the audio
audio_file_address = generate_and_save_multi_speaker_audio(
        api_key=api_key,
        text_prompt=script,
        output_directory="Assets/Genrated_TTS", # Output folder
        model_name="gemini-2.5-flash-preview-tts" # Using the 'flash' model for speed
    )

json_video=get_visual(api_key=api_key,
                      audio_file_path=audio_file_address,
                      orientation=orientation
                      )
json_video=process_sfx_json_and_download(json_video=json_video )

create_video_from_video_clips_and_audio(json_data=json_video,
                                        audio_path=audio_file_address,
                                        orientation=orientation
                                        )

