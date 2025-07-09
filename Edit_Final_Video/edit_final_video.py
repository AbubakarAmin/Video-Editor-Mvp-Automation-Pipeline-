from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips,
    CompositeAudioClip, ImageClip
)
from moviepy.video.fx.all import loop, crop
from datetime import datetime
import os
import uuid
import numpy as np # Import numpy for potential use with audio arrays

def time_to_seconds(t: str) -> float:
    """Converts a time string (MM:SS or MM:SS.sss) to total seconds."""
    try:
        minutes, seconds = t.strip().split(":")
        return int(minutes) * 60 + float(seconds)
    except Exception as e:
        raise ValueError(f"Invalid time format: '{t}'. Must be MM:SS or MM:SS.sss. Error: {e}")

def create_video_from_video_clips_and_audio(
    json_data,
    audio_path: str,
    orientation: str = "landscape",
    output_directory: str = "Assets/Final_Video"
):
    """Creates a final video by combining scene clips, syncing a voiceover, and layering SFX."""
    
    # Set resolution based on orientation
    if orientation == "portrait":
        target_w, target_h = 720, 1280
    elif orientation == "square":
        target_w, target_h = 720, 720
    else:
        target_w, target_h = 1280, 720

    video_clips_for_concat = []
    # Store SFX clips with their intended start times relative to the main video
    sfx_data_for_composite = [] 
    all_video_objects = []
    all_audio_objects = []

    current_video_clip_start_time = 0.0 # Track the start time of the current video segment

    for i, scene in enumerate(json_data):
        try:
            start_sec = time_to_seconds(scene.start_time)
            end_sec = time_to_seconds(scene.end_time)
            scene_duration = end_sec - start_sec

            if scene_duration <= 0:
                print(f"Warning: Scene {i+1} has invalid duration ({scene_duration}s), skipping.")
                continue

            video_path = scene.search_tags_on_pexels
            sfx_path = getattr(scene, "search_tag_for_sfx_from_freesound", None)

            if not os.path.exists(video_path):
                print(f"Warning: Video file '{video_path}' for scene {i+1} not found.")
                continue

            # Load and prepare video
            video_clip = VideoFileClip(video_path)
            all_video_objects.append(video_clip)  # Store for later closing
            original_duration = video_clip.duration

            if original_duration >= scene_duration:
                processed_clip = video_clip.subclip(0, scene_duration)
            else:
                loops = int(scene_duration // original_duration) + 1
                processed_clip = loop(video_clip, n=loops).subclip(0, scene_duration)

            # Resize and crop to match resolution
            processed_clip = processed_clip.resize(height=target_h)
            if processed_clip.w > target_w:
                processed_clip = crop(processed_clip, width=target_w, x_center=processed_clip.w / 2)
            elif processed_clip.w < target_w:
                margin = int((target_w - processed_clip.w) / 2)
                processed_clip = processed_clip.margin(left=margin, right=margin, color=(0, 0, 0))

            processed_clip = processed_clip.set_duration(scene_duration).fadein(0.3).fadeout(0.3)
            video_clips_for_concat.append(processed_clip)

            # Load and process SFX (optional)
            if sfx_path:
                if not os.path.exists(sfx_path):
                    print(f"Warning: SFX file '{sfx_path}' for scene {i+1} not found, skipping.")
                else:
                    sfx_clip = AudioFileClip(sfx_path)
                    all_audio_objects.append(sfx_clip)

                    if sfx_clip.duration >= scene_duration:
                        sfx_trimmed = sfx_clip.subclip(0, scene_duration)
                    else:
                        loops = int(scene_duration // sfx_clip.duration) + 1
                        sfx_trimmed = loop(sfx_clip, n=loops).subclip(0, scene_duration)

                    sfx_trimmed = sfx_trimmed.volumex(0.4)
                    
                    # Store the SFX clip and its intended start time
                    sfx_data_for_composite.append({"clip": sfx_trimmed, "start": current_video_clip_start_time})

            current_video_clip_start_time += scene_duration

        except Exception as e:
            print(f"Error in scene {i+1}: {e}")
            continue

    if not video_clips_for_concat:
        raise ValueError("No valid video clips found.")

    final_video = concatenate_videoclips(video_clips_for_concat, method="compose")

    # Load main voiceover
    try:
        main_audio_clip = AudioFileClip(audio_path)
        all_audio_objects.append(main_audio_clip)
    except Exception as e:
        raise IOError(f"Failed to load main audio '{audio_path}': {e}")

    video_duration = final_video.duration
    audio_duration = main_audio_clip.duration

    # If audio longer than video, pad video with last frame
    if video_duration < audio_duration:
        print("Video shorter than audio — padding with frozen frame...")
        # Ensure last_frame has the correct FPS to avoid audio/video sync issues
        last_frame = final_video.to_ImageClip(t=video_duration - 0.001).set_duration(audio_duration - video_duration).set_fps(final_video.fps)
        final_video = concatenate_videoclips([final_video, last_frame], method="compose")
    elif video_duration > audio_duration:
        print("Video longer than audio — trimming video...")
        final_video = final_video.subclip(0, audio_duration)

    # Now, set the start times for SFX clips relative to the concatenated video
    sfx_clips_with_starts = []
    for sfx_item in sfx_data_for_composite:
        sfx_clips_with_starts.append(sfx_item["clip"].set_start(sfx_item["start"]))

    # Combine all audio tracks
    main_audio_clip = main_audio_clip.set_duration(final_video.duration)
    # Add the main audio clip to the list for composite
    sfx_clips_with_starts.append(main_audio_clip)

    composite_audio = CompositeAudioClip(sfx_clips_with_starts).set_duration(final_video.duration)
    final_video = final_video.set_audio(composite_audio)

    # Export
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, f"final_video_{uuid.uuid4().hex[:8]}.mp4")
    print(f"Rendering video: {output_path}")

    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=24,
        preset="medium",
        threads=os.cpu_count()
    )

    # Cleanup resources
    final_video.close()
    for v in all_video_objects:
        v.close()
    for a in all_audio_objects:
        a.close()

    print("✅ Video creation complete.")
    return output_path