from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from datetime import datetime
import os
import uuid

def time_to_seconds(t):
    """Convert mm:ss or m:ss string to total seconds (int/float)."""
    try:
        return int(datetime.strptime(t, "%M:%S").minute) * 60 + int(datetime.strptime(t, "%M:%S").second)
    except:
        m, s = t.split(":")
        return int(m) * 60 + float(s)

def create_video_from_images_and_audio(json_data, audio_path:str, output_directory:str="Assets/Final_Video"):
    clips = []

    for scene in json_data:
        start = time_to_seconds(scene.start_time)
        end = time_to_seconds(scene.end_time)
        duration = end - start

        image_path = scene.visual
        if not os.path.exists(image_path):
            print(f"Warning Visual: {image_path} not found, skipping.")
            continue

        # Create video clip for this image
        img_clip = (
            ImageClip(image_path)
            .set_duration(duration)
            .set_start(start)
            .fadein(0.3)
            .fadeout(0.3)
            .resize(height=720)  # Resize to fit standard HD if needed
        )

        clips.append(img_clip)

    if not clips:
        raise ValueError("No valid image clips found to create video.")
    fps=24
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.fps = fps

    # Ensure the directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Now build the full output file path
    output_file_path = os.path.join(output_directory, f"final_video_{uuid.uuid4().hex[:8]}.mp4")

    #add audio
    audio_clip = AudioFileClip(audio_path)
    final_video = final_video.set_audio(audio_clip)

    # Export video
    final_video.write_videofile(output_file_path, codec="libx264", audio_codec="aac")

    return output_file_path
