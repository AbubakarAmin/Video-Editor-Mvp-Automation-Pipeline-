import whisper

def get_audio_timestaps(audio_file_path: str):
    model = whisper.load_model("base")  # or "base", "medium", etc.
    result = model.transcribe(audio_file_path)
    return result