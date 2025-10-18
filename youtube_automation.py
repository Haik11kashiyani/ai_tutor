import json
import os
import requests
import time
from pathlib import Path
from moviepy.editor import (
    VideoClip, TextClip, CompositeVideoClip, 
    ColorClip, ImageClip, AudioFileClip, AudioClip
)
from moviepy.video.fx import fadein, fadeout
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

class YouTubeAutomation:
    def __init__(self):
        # ElevenLabs API keys (rotate when quota exhausted)
        self.elevenlabs_keys = [
            os.getenv('ELEVENLABS_KEY_1'),
            os.getenv('ELEVENLABS_KEY_2'),
            os.getenv('ELEVENLABS_KEY_3')
        ]
        self.current_key_index = 0
        
        # Paths
        self.output_folder = Path("output")
        self.output_folder.mkdir(exist_ok=True)
        
        # Video settings for trending shorts
        self.width = 1080
        self.height = 1920  # 9:16 for shorts
        self.fps = 30
        
        # Trending colors and styles
        self.color_schemes = [
            {"bg": "#0F172A", "accent": "#3B82F6", "text": "#F1F5F9", "code_bg": "#1E293B"},
            {"bg": "#1A1A2E", "accent": "#16213E", "text": "#EAEAEA", "code_bg": "#0F3460"},
            {"bg": "#000000", "accent": "#FFD700", "text": "#FFFFFF", "code_bg": "#1C1C1C"},
            {"bg": "#2D1B69", "accent": "#F65A83", "text": "#FFFFFF", "code_bg": "#1E1548"},
        ]

    def load_content(self, json_path="content.json"):
        """Load content from JSON file"""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data['days']

    def generate_script(self, day_data):
        """Generate engaging teacher-like script"""
        title = day_data['title']
        code = day_data['code']
        day = day_data['day']
        
        scripts = [
            f"Hey coders! Welcome to Day {day}. Today we're learning {title}. "
            f"This is super important, so pay attention! "
            f"Here's the code. Let me break it down for you. "
            f"{self._explain_code(code, title)} "
            f"Pretty cool, right? Practice this and you'll master it! "
            f"Like and follow for Day {day + 1}!",
            
            f"What's up everyone! Day {day} is here! "
            f"Today's topic: {title}. This is going to be awesome! "
            f"Check out this code. "
            f"{self._explain_code(code, title)} "
            f"See how simple that is? Now you try it! "
            f"Drop a like if you learned something new!",
            
            f"Yo! Day {day} of our coding journey! "
            f"Let's talk about {title}. This is a game-changer! "
            f"Look at this code right here. "
            f"{self._explain_code(code, title)} "
            f"That's all there is to it! Keep coding, keep growing! "
            f"Follow for more daily coding tips!"
        ]
        
        return random.choice(scripts)

    def _explain_code(self, code, title):
        """Generate code explanation"""
        explanations = {
            "print": "The print function displays output to the screen. Whatever you put inside the quotes will show up when you run the program.",
            "variable": "Variables store data. Think of them as labeled containers that hold information you can use later.",
            "loop": "Loops let you repeat code multiple times without writing it over and over. Super efficient!",
            "function": "Functions are reusable blocks of code. Write once, use anywhere!",
            "list": "Lists store multiple items in a single variable. They're like a shopping list for your data!",
            "if": "If statements make decisions in your code. They check conditions and run code based on the result.",
        }
        
        for key, explanation in explanations.items():
            if key in title.lower() or key in code.lower():
                return explanation
        
        return f"This code demonstrates {title}. It's a fundamental concept every programmer should know!"

    def text_to_speech_elevenlabs(self, text, output_path):
        """Convert text to speech using ElevenLabs with key rotation"""
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        for attempt in range(len(self.elevenlabs_keys)):
            api_key = self.elevenlabs_keys[self.current_key_index]
            
            if not api_key:
                print(f"⚠️  API key {self.current_key_index + 1} not set, trying next...")
                self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
                continue
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            try:
                response = requests.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Audio generated with API key {self.current_key_index + 1}")
                    return True
                elif response.status_code == 401:
                    print(f"✗ API key {self.current_key_index + 1} quota exhausted, rotating...")
                    self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
                else:
                    print(f"Error: {response.status_code}")
                    return False
            except Exception as e:
                print(f"Error with key {self.current_key_index + 1}: {e}")
                self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
        
        print("All API keys exhausted or unavailable!")
        return False

    def create_code_image(self, code, day, scheme):
        """Create professional code snippet image"""
        img = Image.new('RGB', (900, 600), scheme['code_bg'])
        draw = ImageDraw.Draw(img)
        
        try:
            font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)
            font_day = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        except:
            font_code = ImageFont.load_default()
            font_day = ImageFont.load_default()
        
        # Day badge
        draw.rounded_rectangle([30, 30, 200, 100], radius=15, fill=scheme['accent'])
        draw.text((115, 65), f"DAY {day}", fill=scheme['text'], font=font_day, anchor="mm")
        
        # Code with syntax-like highlighting
        y_offset = 180
        for line in code.split('\n'):
            # Simple syntax coloring
            if 'print' in line or 'def' in line or 'class' in line:
                color = '#F472B6'  # Pink for keywords
            elif '"' in line or "'" in line:
                color = '#34D399'  # Green for strings
            else:
                color = scheme['text']
            
            draw.text((50, y_offset), line, fill=color, font=font_code)
            y_offset += 60
        
        return img

    def create_video(self, day_data, audio_path, scheme):
        """Create engaging video with animations"""
        # Load audio to get duration first
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        # Background with gradient effect
        bg_clip = ColorClip(size=(self.width, self.height), color=scheme['bg'], duration=duration)
        
        # Create code image
        code_img = self.create_code_image(day_data['code'], day_data['day'], scheme)
        code_img_path = self.output_folder / f"temp_code_{day_data['day']}.png"
        code_img.save(str(code_img_path))
        
        # Code image with proper sizing
        code_clip = (ImageClip(str(code_img_path))
                    .set_duration(duration)
                    .resize(width=int(self.width * 0.85))
                    .set_position('center')
                    .fadein(0.5)
                    .fadeout(0.5))
        
        # Animated title with proper text wrapping
        title_text = f"Day {day_data['day']}: {day_data['title']}"
        try:
            title = (TextClip(title_text, fontsize=60, color=scheme['text'], 
                             font='DejaVu-Sans-Bold', stroke_color=scheme['accent'], 
                             stroke_width=2, size=(self.width-100, None), method='caption')
                    .set_position(('center', 100))
                    .set_duration(duration)
                    .fadein(0.5))
        except Exception as e:
            print(f"Warning: Could not create title with effects: {e}")
            title = (TextClip(title_text, fontsize=60, color=scheme['text'], 
                             font='DejaVu-Sans-Bold', size=(self.width-100, None), method='caption')
                    .set_position(('center', 100))
                    .set_duration(duration)
                    .fadein(0.5))
        
        # Call-to-action overlay
        cta_text = f"👍 LIKE & FOLLOW for Day {day_data['day'] + 1}"
        try:
            cta = (TextClip(cta_text, fontsize=45, color=scheme['text'],
                           font='DejaVu-Sans-Bold', bg_color=scheme['accent'],
                           size=(self.width-100, None), method='caption')
                  .set_position(('center', self.height-200))
                  .set_start(max(0, duration-3))
                  .set_duration(min(3, duration))
                  .fadein(0.5))
        except Exception as e:
            print(f"Warning: Could not create CTA: {e}")
            cta = None
        
        # Compose video
        if cta:
            video = CompositeVideoClip([bg_clip, code_clip, title, cta], size=(self.width, self.height))
        else:
            video = CompositeVideoClip([bg_clip, code_clip, title], size=(self.width, self.height))
        
        video = video.set_audio(audio)
        
        return video

    def generate_youtube_metadata(self, day_data):
        """Generate SEO-optimized YouTube metadata"""
        title = f"Day {day_data['day']}: {day_data['title']} | Python Tutorial #shorts #viral #programming"
        
        description = f"""🔥 Day {day_data['day']} of our 30-Day Coding Challenge! 

Today's Topic: {day_data['title']}

Code:
{day_data['code']}

💡 Master this concept and level up your programming skills!

👉 Follow for Day {day_data['day'] + 1}!

#python #coding #programming #shorts #viral #codingtutorial #pythonforbeginners 
#learnpython #pythonprogramming #codingshorts #programmingshorts #techeducation
#softwareengineering #developer #webdevelopment #pythontutorial #codinglife
#100daysofcode #dailycode #codingchallenge

⏰ 30 Days of Python - Don't miss a day!
📚 Perfect for beginners and intermediate programmers
🚀 Quick, easy-to-understand explanations

Subscribe and turn on notifications! 🔔"""

        tags = [
            "python", "programming", "coding", "tutorial", "shorts",
            "python tutorial", "learn python", "coding for beginners",
            "python programming", "software development", "tech education",
            "programming tutorial", "coding shorts", "viral shorts",
            f"day {day_data['day']}", "30 day challenge", "daily coding"
        ]
        
        return {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "category": "27",
            "privacyStatus": "public"
        }

    def create_all_videos(self, json_path="content.json", language="python"):
        """Generate all videos from JSON"""
        days = self.load_content(json_path)
        
        for day_data in days:
            print(f"\n{'='*50}")
            print(f"Processing Day {day_data['day']}: {day_data['title']}")
            print(f"{'='*50}")
            
            scheme = random.choice(self.color_schemes)
            script = automation.generate_script(day_data)
            print(f"📝 Script generated: {len(script)} characters")
            
            audio_path = self.output_folder / f"day_{day_data['day']}_audio.mp3"
            audio_success = self.text_to_speech_elevenlabs(script, str(audio_path))
            
            if not audio_success:
                print(f"⚠️  Creating silent audio as fallback...")
                silent = AudioClip(lambda t: 0, duration=5, fps=44100)
                silent.write_audiofile(str(audio_path))
            
            print("🎬 Creating video...")
            video = self.create_video(day_data, audio_path, scheme)
            
            video_path = self.output_folder / f"day_{day_data['day']}_{language}.mp4"
            video.write_videofile(
                str(video_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                bitrate='3000k'
            )
            
            print(f"✅ Video saved: {video_path}")
            
            metadata = self.generate_youtube_metadata(day_data)
            metadata_path = self.output_folder / f"day_{day_data['day']}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📄 Metadata saved: {metadata_path}")
            
            if (self.output_folder / f"temp_code_{day_data['day']}.png").exists():
                (self.output_folder / f"temp_code_{day_data['day']}.png").unlink()
            
            time.sleep(2)

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.create_all_videos("content.json", language="python")
    
    print("\n" + "="*50)
    print("✨ ALL VIDEOS GENERATED SUCCESSFULLY!")
    print("="*50)
    print(f"📁 Videos saved in: {automation.output_folder}")
    print("🚀 Ready for YouTube upload!")
