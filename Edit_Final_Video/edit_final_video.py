from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips,
    CompositeAudioClip, ImageClip
)
from moviepy.video.fx.all import loop, crop
from datetime import datetime
import os
import uuid
import numpy as np

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

            # Load and process SFX (optional) with improved error handling
            if sfx_path and os.path.exists(sfx_path):
                try:
                    sfx_clip = AudioFileClip(sfx_path)
                    all_audio_objects.append(sfx_clip)
                    
                    # Ensure SFX duration matches scene duration
                    if sfx_clip.duration >= scene_duration:
                        sfx_trimmed = sfx_clip.subclip(0, scene_duration)
                    else:
                        loops = int(scene_duration // sfx_clip.duration) + 1
                        sfx_trimmed = loop(sfx_clip, n=loops).subclip(0, scene_duration)

                    # Apply volume reduction and ensure exact duration
                    sfx_trimmed = sfx_trimmed.volumex(0.5).set_duration(scene_duration)
                    
                    # Store the SFX clip and its intended start time
                    sfx_data_for_composite.append({
                        "clip": sfx_trimmed, 
                        "start": current_video_clip_start_time
                    })
                        
                except Exception as e:
                    print(f"Warning: Failed to load SFX file '{sfx_path}' for scene {i+1}: {e}")

            current_video_clip_start_time += scene_duration

        except Exception as e:
            print(f"Error in scene {i+1}: {e}")
            continue

    if not video_clips_for_concat:
        raise ValueError("No valid video clips found.")

    # Concatenate all video clips
    final_video = concatenate_videoclips(video_clips_for_concat, method="compose")

    # Load main voiceover with error handling
    try:
        main_audio_clip = AudioFileClip(audio_path)
        all_audio_objects.append(main_audio_clip)
            
    except Exception as e:
        raise IOError(f"Failed to load main audio '{audio_path}': {e}")

    video_duration = final_video.duration
    audio_duration = main_audio_clip.duration

    # Sync video and audio durations
    if video_duration < audio_duration:
        print("Video shorter than audio — padding with frozen frame...")
        # Ensure last_frame has the correct FPS to avoid audio/video sync issues
        last_frame = final_video.to_ImageClip(t=video_duration - 0.001).set_duration(audio_duration - video_duration).set_fps(final_video.fps)
        final_video = concatenate_videoclips([final_video, last_frame], method="compose")
    elif video_duration > audio_duration:
        print("Video longer than audio — trimming video...")
        final_video = final_video.subclip(0, audio_duration)

    # Update video duration after adjustment
    final_video_duration = final_video.duration

    # THE KEY FIX: Create composite audio more carefully
    try:
        # Start with main audio - set exact duration first
        main_audio_final = main_audio_clip.subclip(0, min(main_audio_clip.duration, final_video_duration))
        main_audio_final = main_audio_final.set_duration(final_video_duration)
        
        # Process SFX clips with strict bounds checking
        valid_sfx_clips = []
        for sfx_item in sfx_data_for_composite:
            sfx_clip = sfx_item["clip"]
            start_time = sfx_item["start"]
            
            # Skip if start time is beyond video duration
            if start_time >= final_video_duration:
                continue
                
            # Calculate exact end time and duration
            max_duration = final_video_duration - start_time
            sfx_duration = min(sfx_clip.duration, max_duration)
            
            # Create properly bounded SFX clip
            if sfx_duration > 0:
                bounded_sfx = sfx_clip.subclip(0, sfx_duration).set_start(start_time)
                valid_sfx_clips.append(bounded_sfx)
        
        # Create composite audio with main audio + valid SFX clips
        if valid_sfx_clips:
            all_audio_clips = [main_audio_final] + valid_sfx_clips
            composite_audio = CompositeAudioClip(all_audio_clips)
        else:
            composite_audio = main_audio_final
            
        # Ensure composite audio has exact duration
        composite_audio = composite_audio.set_duration(final_video_duration)
        final_video = final_video.set_audio(composite_audio)
        
        # Final sync check - ensure audio and video durations match exactly
        video_dur = final_video.duration
        audio_dur = final_video.audio.duration
        
        if abs(video_dur - audio_dur) > 0.01:  # Allow 0.01s tolerance
            print(f"Duration mismatch detected: Video={video_dur:.3f}s, Audio={audio_dur:.3f}s")
            
            if video_dur > audio_dur:
                print("Trimming video to match audio duration...")
                final_video = final_video.subclip(0, audio_dur)
            else:
                print("Trimming audio to match video duration...")
                final_video = final_video.set_audio(final_video.audio.subclip(0, video_dur))
        
    except Exception as e:
        print(f"Warning: Failed to create composite audio: {e}")
        print("Using only main audio track...")
        # Fallback to main audio only
        main_audio_safe = main_audio_clip.subclip(0, min(main_audio_clip.duration, final_video_duration))
        main_audio_safe = main_audio_safe.set_duration(final_video_duration)
        final_video = final_video.set_audio(main_audio_safe)
        
        # Final sync check for fallback case
        video_dur = final_video.duration
        audio_dur = final_video.audio.duration
        
        if abs(video_dur - audio_dur) > 0.01:
            print(f"Fallback duration mismatch: Video={video_dur:.3f}s, Audio={audio_dur:.3f}s")
            
            if video_dur > audio_dur:
                final_video = final_video.subclip(0, audio_dur)
            else:
                final_video = final_video.set_audio(final_video.audio.subclip(0, video_dur))

    # Export with standard settings
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, f"final_video_{uuid.uuid4().hex[:8]}.mp4")
    print(f"Rendering video: {output_path}")

    try:
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="medium",
            threads=os.cpu_count(),
            verbose=False,
            logger=None
        )
    except Exception as e:
        print(f"Error during video export: {e}")
        # Try simpler export settings
        print("Trying simplified export settings...")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="fast",
            threads=1,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )

    # Cleanup resources
    try:
        final_video.close()
        for v in all_video_objects:
            v.close()
        for a in all_audio_objects:
            a.close()
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")

    print("✅ Video creation complete.")
    return output_path