from TTS.genrate_audio import generate_and_save_multi_speaker_audio
from Transcribe_Audio.transcribe_audio import get_audio_timestaps
from Get_Visuals.get_visuals_description_for_auido import get_visual
from dotenv import load_dotenv
import os
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY") 




conversation_text = """Whispery, introspective, and heavy with emotion.Slightly trembled, as if revealing a long-held truth.Quiet but intense — like a conversation at midnight, just before something changes forever.:
Speaker 1 (Woman): (soft, reflective) Funny, isn’t it? (pause) How a single train... can carry years of silence. (pause, deeper) I waited here. Every night. Just in case... you'd come back.

Speaker 2 (Man): (low, regretful) I never stopped thinking about this platform. (sigh) The sound of your steps… the way the light caught your face. (pause) I left... but I never really left you.

Speaker 1: (whispers, almost a plea) Then why did it take so long? (pause) The letters stopped. So did time. (fragile) I counted winters. Alone.

Speaker 2: (pained, firm) I was scared. Of what I’d see"""

    # Call the function to generate and save the audio
file_address = generate_and_save_multi_speaker_audio(
        api_key=api_key,
        text_prompt=conversation_text,
        output_directory="Genrated_TTS", # Output folder
        model_name="gemini-2.5-flash-preview-tts" # Using the 'flash' model for speed
    )
# trascribed_text=get_audio_timestaps(file_address)
# print(trascribed_text)

description=get_visual(api_key=api_key,audio_file_path=file_address)
print (description)
