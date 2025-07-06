from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.all import loop, crop
from datetime import datetime
import os
import uuid

def time_to_seconds(t):
    try:
        return int(datetime.strptime(t, "%M:%S").minute) * 60 + int(datetime.strptime(t, "%M:%S").second)
    except:
        m, s = t.split(":")
        return int(m) * 60 + float(s)

def create_video_from_video_clips_and_audio(json_data, audio_path: str, orientation: str = "landscape", output_directory: str = "Assets/Final_Video"):
    # Set output resolution
    if orientation == "portrait":
        target_w, target_h = 720, 1280
    elif orientation == "square":
        target_w, target_h = 720, 720
    else:  # landscape default
        target_w, target_h = 1280, 720

    clips = []

    for scene in json_data:
        start = time_to_seconds(scene.start_time)
        end = time_to_seconds(scene.end_time)
        duration = end - start

        video_path = scene.search_tags_on_pixels
        if not os.path.exists(video_path):
            print(f"Warning: Video {video_path} not found, skipping.")
            continue

        try:
            base_clip = VideoFileClip(video_path)
            clip_duration = base_clip.duration

            if clip_duration >= duration:
                clip = base_clip.subclip(0, duration)
            else:
                # Loop to fit target duration
                loops_required = int(duration // clip_duration) + 1
                clip = loop(base_clip, n=loops_required).subclip(0, duration)

            # Resize based on orientation
            clip = clip.resize(height=target_h)

            # Crop or pad to exact width
            if clip.w > target_w:
                clip = crop(clip, width=target_w, x_center=clip.w / 2)
            elif clip.w < target_w:
                margin = (target_w - clip.w) // 2
                clip = clip.margin(left=margin, right=margin, color=(0, 0, 0))

            clip = clip.set_duration(duration).fadein(0.3).fadeout(0.3)
            clips.append(clip)

        except Exception as e:
            print(f"Error processing {video_path}: {e}")
            continue

    if not clips:
        raise ValueError("No valid video clips found.")

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(AudioFileClip(audio_path))

    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, f"final_video_{uuid.uuid4().hex[:8]}.mp4")

    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    return output_path
