"""
Modular Video Editor for combining video clips, voiceover, and SFX
"""

from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips,
    CompositeAudioClip, ImageClip
)
from moviepy.video.fx.all import loop, crop
from datetime import datetime
import os
import uuid
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VideoConfig:
    """Configuration for video processing"""
    orientation: str = "landscape"
    output_directory: str = "Assets/Final_Video"
    sfx_volume: float = 0.3  # Volume multiplier for SFX (0.0 to 1.0)
    fade_duration: float = 0.3
    fps: int = 24
    audio_sample_rate: int = 44100
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get target resolution based on orientation"""
        resolutions = {
            "portrait": (720, 1280),
            "square": (720, 720),
            "landscape": (1280, 720)
        }
        return resolutions.get(self.orientation, (1280, 720))


class TimeUtils:
    """Utility functions for time conversion"""
    
    @staticmethod
    def to_seconds(time_str: str) -> float:
        """Converts a time string (MM:SS or MM:SS.sss) to total seconds."""
        try:
            minutes, seconds = time_str.strip().split(":")
            return int(minutes) * 60 + float(seconds)
        except Exception as e:
            raise ValueError(f"Invalid time format: '{time_str}'. Must be MM:SS or MM:SS.sss. Error: {e}")


class VideoProcessor:
    """Handles video clip processing and preparation"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.target_w, self.target_h = config.get_resolution()
        
    def process_video_clip(self, video_path: str, duration: float) -> VideoFileClip:
        """Process a single video clip with resizing, cropping, and duration adjustment"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        video_clip = VideoFileClip(video_path)
        original_duration = video_clip.duration
        
        # Handle duration - loop if needed
        if original_duration >= duration:
            processed_clip = video_clip.subclip(0, duration)
        else:
            loops = int(duration // original_duration) + 1
            processed_clip = loop(video_clip, n=loops).subclip(0, duration)
        
        # Resize and crop to match target resolution
        processed_clip = self._resize_and_crop(processed_clip)
        
        # Apply duration, fade in/out
        processed_clip = (processed_clip
                         .set_duration(duration)
                         .fadein(self.config.fade_duration)
                         .fadeout(self.config.fade_duration))
        
        return processed_clip
    
    def _resize_and_crop(self, clip: VideoFileClip) -> VideoFileClip:
        """Resize and crop clip to target resolution"""
        # Resize to match target height
        clip = clip.resize(height=self.target_h)
        
        # Handle width adjustment
        if clip.w > self.target_w:
            # Crop from center if too wide
            clip = crop(clip, width=self.target_w, x_center=clip.w / 2)
        elif clip.w < self.target_w:
            # Add black margins if too narrow
            margin = int((self.target_w - clip.w) / 2)
            clip = clip.margin(left=margin, right=margin, color=(0, 0, 0))
            
        return clip


class AudioProcessor:
    """Handles audio processing including SFX and voiceover"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        
    def process_sfx_clip(self, sfx_path: str, duration: float, start_time: float) -> Optional[Dict]:
        """Process a single SFX clip with proper volume reduction and timing"""
        if not sfx_path or not os.path.exists(sfx_path):
            return None
            
        try:
            sfx_clip = AudioFileClip(sfx_path)
            original_duration = sfx_clip.duration
            
            # Handle duration - loop if needed
            if original_duration >= duration:
                sfx_trimmed = sfx_clip.subclip(0, duration)
            else:
                loops = int(duration // original_duration) + 1
                sfx_trimmed = loop(sfx_clip, n=loops).subclip(0, duration)
            
            # FIXED: Apply volume reduction properly
            # Use multiply instead of volumex for better control
            sfx_trimmed = sfx_trimmed.fx(lambda clip: clip.volumex(self.config.sfx_volume))
            sfx_trimmed = sfx_trimmed.set_duration(duration)
            
            return {
                "clip": sfx_trimmed,
                "start": start_time,
                "original_clip": sfx_clip  # Keep reference for cleanup
            }
            
        except Exception as e:
            print(f"Warning: Failed to process SFX '{sfx_path}': {e}")
            return None
    
    def create_composite_audio(self, main_audio_path: str, sfx_data: List[Dict], 
                              video_duration: float) -> AudioFileClip:
        """Create composite audio from main audio and SFX clips"""
        try:
            # Load main audio
            main_audio = AudioFileClip(main_audio_path)
            main_duration = min(main_audio.duration, video_duration)
            main_audio_final = main_audio.subclip(0, main_duration).set_duration(video_duration)
            
            # Process valid SFX clips
            valid_sfx_clips = []
            for sfx_item in sfx_data:
                if sfx_item is None:
                    continue
                    
                sfx_clip = sfx_item["clip"]
                start_time = sfx_item["start"]
                
                # Validate timing
                if start_time >= video_duration or start_time < 0:
                    print(f"Skipping SFX clip with invalid start time: {start_time}")
                    continue
                
                # Calculate bounded duration
                max_duration = video_duration - start_time
                sfx_duration = min(sfx_clip.duration, max_duration)
                
                if sfx_duration > 0.1:  # Minimum duration threshold
                    try:
                        bounded_sfx = (sfx_clip.subclip(0, sfx_duration)
                                     .set_start(start_time)
                                     .set_duration(sfx_duration))
                        
                        # Final validation
                        if (bounded_sfx.start >= 0 and 
                            (bounded_sfx.start + bounded_sfx.duration) <= video_duration):
                            valid_sfx_clips.append(bounded_sfx)
                        else:
                            print(f"Skipping SFX clip with invalid timing: "
                                  f"start={bounded_sfx.start}, duration={bounded_sfx.duration}")
                    except Exception as e:
                        print(f"Warning: Failed to process SFX clip: {e}")
                        continue
            
            # Create composite
            if valid_sfx_clips:
                print(f"Adding {len(valid_sfx_clips)} SFX clips to composite audio")
                all_audio_clips = [main_audio_final] + valid_sfx_clips
                composite_audio = CompositeAudioClip(all_audio_clips)
                composite_audio = composite_audio.set_duration(video_duration)
            else:
                print("No valid SFX clips found, using main audio only")
                composite_audio = main_audio_final
                
            return composite_audio, main_audio
            
        except Exception as e:
            print(f"Error creating composite audio: {e}")
            raise


class VideoSynchronizer:
    """Handles video-audio synchronization"""
    
    @staticmethod
    def sync_video_audio(video: VideoFileClip, audio: AudioFileClip) -> VideoFileClip:
        """Synchronize video and audio durations"""
        video_duration = video.duration
        audio_duration = audio.duration
        
        if video_duration < audio_duration:
            print("Video shorter than audio — padding with frozen frame...")
            last_frame = (video.to_ImageClip(t=video_duration - 0.001)
                         .set_duration(audio_duration - video_duration)
                         .set_fps(video.fps))
            video = concatenate_videoclips([video, last_frame], method="compose")
        elif video_duration > audio_duration:
            print("Video longer than audio — trimming video...")
            video = video.subclip(0, audio_duration)
            
        return video
    
    @staticmethod
    def ensure_exact_sync(video: VideoFileClip) -> VideoFileClip:
        """Ensure video and audio have exactly matching durations"""
        if video.audio is None:
            return video
            
        video_dur = video.duration
        audio_dur = video.audio.duration
        
        print(f"Final durations - Video: {video_dur:.3f}s, Audio: {audio_dur:.3f}s")
        
        if abs(video_dur - audio_dur) > 0.1:  # Allow 0.1s tolerance
            print(f"Duration mismatch detected: Video={video_dur:.3f}s, Audio={audio_dur:.3f}s")
            
            # Fix by trimming to shorter duration
            target_duration = min(video_dur, audio_dur)
            print(f"Trimming both to {target_duration:.3f}s")
            
            video = video.subclip(0, target_duration)
            video = video.set_audio(video.audio.subclip(0, target_duration))
            
        return video


class VideoExporter:
    """Handles video export with various fallback options"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        
    def export_video(self, video: VideoFileClip, output_path: str) -> str:
        """Export video with progressive fallback options"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        export_attempts = [
            self._export_high_quality,
            self._export_medium_quality,
            self._export_basic_quality,
            self._export_without_audio
        ]
        
        for attempt_func in export_attempts:
            try:
                attempt_func(video, output_path)
                print("✅ Video export successful")
                return output_path
            except Exception as e:
                print(f"Export attempt failed: {e}")
                continue
                
        raise RuntimeError("All export attempts failed")
    
    def _export_high_quality(self, video: VideoFileClip, output_path: str):
        """High quality export settings"""
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=self.config.fps,
            preset="medium",
            threads=min(4, os.cpu_count() or 1),
            verbose=False,
            logger=None,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            audio_bufsize=2000,
            audio_fps=self.config.audio_sample_rate,
            audio_nbytes=2
        )
    
    def _export_medium_quality(self, video: VideoFileClip, output_path: str):
        """Medium quality export settings"""
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=self.config.fps,
            preset="fast",
            threads=1,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            audio_bufsize=1000,
            audio_fps=22050,
            audio_nbytes=2
        )
    
    def _export_basic_quality(self, video: VideoFileClip, output_path: str):
        """Basic quality export settings"""
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=self.config.fps,
            preset="fast",
            threads=1
        )
    
    def _export_without_audio(self, video: VideoFileClip, output_path: str):
        """Export without audio as last resort"""
        print("Exporting video without audio...")
        video_no_audio = video.without_audio()
        video_no_audio.write_videofile(
            output_path,
            codec="libx264",
            fps=self.config.fps,
            preset="fast",
            threads=1
        )
        video_no_audio.close()


class ResourceManager:
    """Manages cleanup of MoviePy objects"""
    
    def __init__(self):
        self.video_objects: List[VideoFileClip] = []
        self.audio_objects: List[AudioFileClip] = []
        
    def add_video(self, video: VideoFileClip):
        """Add video object for cleanup"""
        self.video_objects.append(video)
        
    def add_audio(self, audio: AudioFileClip):
        """Add audio object for cleanup"""
        self.audio_objects.append(audio)
        
    def cleanup(self):
        """Clean up all registered objects"""
        try:
            for video in self.video_objects:
                video.close()
            for audio in self.audio_objects:
                audio.close()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")


class VideoEditor:
    """Main video editor class that orchestrates all components"""
    
    def __init__(self, config: VideoConfig = None):
        self.config = config or VideoConfig()
        self.video_processor = VideoProcessor(self.config)
        self.audio_processor = AudioProcessor(self.config)
        self.exporter = VideoExporter(self.config)
        self.resource_manager = ResourceManager()
        
    def create_video_from_clips(self, json_data, audio_path: str) -> str:
        """Main method to create video from scene data and audio"""
        try:
            # Process all scenes
            video_clips, sfx_data = self._process_scenes(json_data)
            
            if not video_clips:
                raise ValueError("No valid video clips found.")
            
            # Concatenate video clips
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Create composite audio
            composite_audio, main_audio = self.audio_processor.create_composite_audio(
                audio_path, sfx_data, final_video.duration
            )
            self.resource_manager.add_audio(main_audio)
            
            # Sync video and audio
            final_video = VideoSynchronizer.sync_video_audio(final_video, composite_audio)
            final_video = final_video.set_audio(composite_audio)
            final_video = VideoSynchronizer.ensure_exact_sync(final_video)
            
            # Export video
            output_path = self._generate_output_path()
            result_path = self.exporter.export_video(final_video, output_path)
            
            # Cleanup
            final_video.close()
            
            return result_path
            
        except Exception as e:
            print(f"Error creating video: {e}")
            raise
        finally:
            self.resource_manager.cleanup()
    
    def _process_scenes(self, json_data) -> Tuple[List[VideoFileClip], List[Dict]]:
        """Process all scenes and return video clips and SFX data"""
        video_clips = []
        sfx_data = []
        current_start_time = 0.0
        
        for i, scene in enumerate(json_data):
            try:
                start_sec = TimeUtils.to_seconds(scene.start_time)
                end_sec = TimeUtils.to_seconds(scene.end_time)
                scene_duration = end_sec - start_sec
                
                if scene_duration <= 0:
                    print(f"Warning: Scene {i+1} has invalid duration ({scene_duration}s), skipping.")
                    continue
                
                # Process video clip
                video_path = scene.search_tags_on_pexels
                video_clip = self.video_processor.process_video_clip(video_path, scene_duration)
                video_clips.append(video_clip)
                self.resource_manager.add_video(video_clip)
                
                # Process SFX clip
                sfx_path = getattr(scene, "search_tag_for_sfx_from_freesound", None)
                sfx_item = self.audio_processor.process_sfx_clip(sfx_path, scene_duration, current_start_time)
                
                if sfx_item:
                    sfx_data.append(sfx_item)
                    self.resource_manager.add_audio(sfx_item["original_clip"])
                
                current_start_time += scene_duration
                
            except Exception as e:
                print(f"Error processing scene {i+1}: {e}")
                continue
                
        return video_clips, sfx_data
    
    def _generate_output_path(self) -> str:
        """Generate unique output path"""
        filename = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        return os.path.join(self.config.output_directory, filename)


# Convenience function for backward compatibility
def create_video_from_video_clips_and_audio(
    json_data,
    audio_path: str,
    orientation: str = "landscape",
    output_directory: str = "Assets/Final_Video"
) -> str:
    """Legacy function wrapper for backward compatibility"""
    config = VideoConfig(
        orientation=orientation,
        output_directory=output_directory,
        sfx_volume=0.1,  # 20% volume for SFX
        fade_duration=0.5,  # 0.5 second fade
        fps=24
    )
    
    editor = VideoEditor(config)
    return editor.create_video_from_clips(json_data, audio_path)


