
import sys
import os
sys.path.append(os.getcwd())
from youtube_automation import YouTubeAutomation
import datetime

def test_visuals():
    print("🚀 Starting Visual Verification...")
    
    # Mock data
    day_data = {
        "day": 99,
        "title": "Scroll Test",
        "language": "python",
        "code": "print('Line 1')\nprint('Line 2')\nprint('Line 3')\nprint('Line 4')\nprint('Line 5')\nprint('Line 6')\nprint('Line 7')\nprint('Line 8')\nprint('Line 9')\nprint('Line 10')\nprint('Line 11')\nprint('Line 12')\nprint('Line 13')\nprint('Line 14')\nprint('Line 15')\nprint('Line 16')\nprint('Line 17')\nprint('Line 18')",
        "output": "Line 1\n...\nLine 18",
        "explanation": "Testing Smart Scroll. The view should follow the typing cursor downwards.",
        "hook": "SCROLL TEST",
        "cta": "CHECK IT"
    }
    
    automation = YouTubeAutomation()
    
    # Override settings for speed
    automation.fps = 15 # Lower FPS for quick test
    duration = 5 # 5 seconds
    
    # Mock audio (silence)
    from moviepy.audio.AudioClip import AudioArrayClip
    import numpy as np
    silence = np.zeros((int(duration * 44100), 2))
    audio_path = "test_audio.mp3"
    
    # Generate Scheme
    scheme = automation.generate_dynamic_theme("Test")
    print(f"🎨 Theme: {scheme}")
    
    print("🎥 Rendering Test Video...")
    video = automation.create_video(day_data, "mock_audio_path_will_fail_but_handled", scheme)
    
    # We need to manually set duration because the mock audio path isn't real and create_video handles it
    # But wait, create_video attempts to load audio. Let's create a real silent audio file.
    silent_clip = AudioArrayClip(silence, fps=44100)
    silent_clip.write_audiofile(audio_path, fps=44100)
    
    video = automation.create_video(day_data, audio_path, scheme)
    
    output_path = "output/test_visuals.mp4"
    video.write_videofile(output_path, fps=15, codec='libx264', audio_codec='aac')
    
    print(f"✅ Video generated at {output_path}")

if __name__ == "__main__":
    test_visuals()
