"""
Test script to generate a single video for testing
Run this first to check video quality before full automation
"""

import json
import os
from youtube_automation import YouTubeAutomation
from moviepy.editor import AudioClip

def test_single_video():
    """Generate a single test video"""
    
    # Check for API key
    if not os.getenv('ELEVENLABS_KEY_1'):
        print("⚠️  WARNING: ELEVENLABS_KEY_1 not set!")
        print("Set it in GitHub Secrets")
        print("\nFor now, continuing with silent video...")
    
    # Initialize automation
    automation = YouTubeAutomation()
    
    # Create test content (Day 1)
    test_content = {
        "day": 1,
        "title": "Print Hello World",
        "code": "print('Hello, World!')",
        "explanation": ""
    }
    
    print("="*60)
    print("🎬 TESTING VIDEO GENERATION")
    print("="*60)
    print(f"\nGenerating test video for Day {test_content['day']}")
    print(f"Title: {test_content['title']}")
    print(f"Code: {test_content['code']}")
    
    # Select color scheme
    import random
    scheme = random.choice(automation.color_schemes)
    print(f"\nColor Scheme: {scheme['bg']} / {scheme['accent']}")
    
    # Generate script
    script = automation.generate_script(test_content)
    print(f"\n📝 Generated Script ({len(script)} chars):")
    print("-" * 60)
    print(script)
    print("-" * 60)
    
    # Generate audio
    audio_path = automation.output_folder / "test_audio.mp3"
    print(f"\n🎙️  Generating voiceover...")
    
    if os.getenv('ELEVENLABS_KEY_1'):
        audio_success = automation.text_to_speech_elevenlabs(script, audio_path)
        if not audio_success:
            print("❌ Failed to generate audio. Creating silent video...")
            # Create silent audio (5 seconds)
            silent = AudioClip(lambda t: 0, duration=5, fps=44100)
            silent.write_audiofile(str(audio_path))
    else:
        print("⚠️  No API key, creating 5-second silent audio...")
        silent = AudioClip(lambda t: 0, duration=5, fps=44100)
        silent.write_audiofile(str(audio_path))
    
    # Create video
    print(f"\n🎥 Creating video...")
    video = automation.create_video(test_content, audio_path, scheme)
    
    # Save video
    video_path = automation.output_folder / "TEST_day_1_python.mp4"
    print(f"\n💾 Saving video to: {video_path}")
    
    video.write_videofile(
        str(video_path),
        fps=automation.fps,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        bitrate='3000k',
        threads=4
    )
    
    # Generate metadata
    metadata = automation.generate_youtube_metadata(test_content)
    metadata_path = automation.output_folder / "TEST_day_1_metadata.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ TEST VIDEO GENERATED SUCCESSFULLY!")
    print("="*60)
    print(f"\n📁 Output Files:")
    print(f"   Video: {video_path}")
    print(f"   Metadata: {metadata_path}")
    print(f"   Audio: {audio_path}")
    
    print("\n📺 YouTube Metadata Preview:")
    print("-" * 60)
    print(f"Title: {metadata['title']}")
    print(f"\nDescription:\n{metadata['description'][:200]}...")
    print(f"\nTags: {', '.join(metadata['tags'][:5])}...")
    print("-" * 60)
    
    print("\n🎉 Next Steps:")
    print("   1. Download the video from Artifacts")
    print("   2. Verify audio and visuals are synced")
    print("   3. Check if animations look smooth")
    print("   4. If satisfied, run full generation workflow")
    
    # Cleanup temp files
    temp_code_path = automation.output_folder / f"temp_code_1.png"
    if temp_code_path.exists():
        temp_code_path.unlink()

if __name__ == "__main__":
    test_single_video()
