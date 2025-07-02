
from google.genai import types
from google import genai
import wave
import os
import uuid


# Set up the wave file to save the output:
def _save_wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   """
   Helper function to save PCM data to a WAV file.
   Matches the 'wave_file' function from the official documentation.
   """
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)
def generate_and_save_multi_speaker_audio(
    api_key: str,
    text_prompt: str,
    output_directory: str = "generated_tts",
    model_name: str = "gemini-2.5-flash-preview-tts"
) -> str | None:
    
    try:
        client = genai.Client(api_key=api_key)
        print(f"Sending request to Gemini TTS model: {model_name}...")
  

        response = client.models.generate_content(
        model=model_name,
        contents=text_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker='Speaker1',
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Kore',
                            )
                        )
                    ),
                    types.SpeakerVoiceConfig(
                        speaker='Speaker2',
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Puck',
                            )
                        )
                    ),
                    ]
                )
            )
        )
        )

        audio_data =  response.candidates[0].content.parts[0].inline_data.data
        os.makedirs(output_directory, exist_ok=True)

        # Generate a unique filename with .wav extension
        unique_filename = f"gemini_tts_{uuid.uuid4().hex}.wav"
        output_filepath = os.path.join(output_directory, unique_filename)

        # Save the audio data using the helper function
        _save_wave_file(output_filepath, audio_data)
        
        print(f"Audio saved successfully to {output_filepath}")
        return os.path.abspath(output_filepath)

    except Exception as e:
        print(f"An error occurred in TTS: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"API Error Response in TTS: {e.response.json()}")
        return None


