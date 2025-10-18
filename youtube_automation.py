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
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
        
        # Trending colors - MORE VIBRANT!
        self.color_schemes = [
            {"bg1": "#667eea", "bg2": "#764ba2", "accent": "#f093fb", "text": "#ffffff", "code_bg": "#2d1b4e", "shadow": "#4a148c"},
            {"bg1": "#f093fb", "bg2": "#f5576c", "accent": "#ffd89b", "text": "#ffffff", "code_bg": "#5e2129", "shadow": "#c2185b"},
            {"bg1": "#4facfe", "bg2": "#00f2fe", "accent": "#43e97b", "text": "#ffffff", "code_bg": "#1a3a52", "shadow": "#0277bd"},
            {"bg1": "#fa709a", "bg2": "#fee140", "accent": "#30cfd0", "text": "#ffffff", "code_bg": "#5e2a0c", "shadow": "#d84315"},
            {"bg1": "#30cfd0", "bg2": "#330867", "accent": "#a8edea", "text": "#ffffff", "code_bg": "#1a1033", "shadow": "#1a237e"},
            {"bg1": "#ff6a00", "bg2": "#ee0979", "accent": "#ffd89b", "text": "#ffffff", "code_bg": "#4d0e2f", "shadow": "#b71c1c"},
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

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def create_gradient_background(self, width, height, color1, color2):
        """Create a beautiful gradient background"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        
        for y in range(height):
            ratio = y / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return img

    def add_glow_effect(self, img, glow_color, blur_radius=15):
        """Add a glow effect around content"""
        # Create a copy for the glow
        glow = img.copy()
        # Apply blur
        glow = glow.filter(ImageFilter.GaussianBlur(blur_radius))
        # Blend with original
        return Image.blend(glow, img, 0.7)

    def create_code_image(self, code, day, scheme):
        """Create STUNNING code snippet with glassmorphism effect"""
        # Larger canvas for glow effects
        img = Image.new('RGB', (950, 700), self.hex_to_rgb(scheme['code_bg']))
        
        # Add subtle pattern/texture
        draw = ImageDraw.Draw(img)
        
        # Draw decorative dots pattern
        for i in range(0, 950, 40):
            for j in range(0, 700, 40):
                if random.random() > 0.7:
                    draw.ellipse([i, j, i+3, j+3], fill=self.hex_to_rgb(scheme['accent']) + (50,))
        
        # Create glassmorphism card
        card_margin = 25
        card = Image.new('RGBA', (900, 650), self.hex_to_rgb(scheme['code_bg']) + (220,))
        card_draw = ImageDraw.Draw(card)
        
        # Add border glow
        border_color = self.hex_to_rgb(scheme['accent'])
        for i in range(5):
            card_draw.rounded_rectangle(
                [i, i, 900-i, 650-i], 
                radius=25, 
                outline=border_color + (50 - i*10,),
                width=2
            )
        
        try:
            font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 42)
            font_day = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font_code = ImageFont.load_default()
            font_day = ImageFont.load_default()
        
        # Day badge with shadow and glow
        badge_x, badge_y = 40, 40
        badge_w, badge_h = 180, 90
        
        # Shadow
        shadow_offset = 8
        card_draw.rounded_rectangle(
            [badge_x+shadow_offset, badge_y+shadow_offset, 
             badge_x+badge_w+shadow_offset, badge_y+badge_h+shadow_offset],
            radius=20, fill=self.hex_to_rgb(scheme['shadow']) + (100,)
        )
        
        # Badge background with gradient effect
        card_draw.rounded_rectangle(
            [badge_x, badge_y, badge_x+badge_w, badge_y+badge_h], 
            radius=20, fill=self.hex_to_rgb(scheme['accent'])
        )
        
        # Badge text with subtle shadow
        day_text = f"DAY {day}"
        bbox = card_draw.textbbox((0, 0), day_text, font=font_day)
        text_w = bbox[2] - bbox[0]
        text_x = badge_x + (badge_w - text_w) // 2
        text_y = badge_y + 20
        
        # Text shadow
        card_draw.text((text_x+3, text_y+3), day_text, fill=(0, 0, 0, 120), font=font_day)
        # Main text
        card_draw.text((text_x, text_y), day_text, fill='#ffffff', font=font_day)
        
        # Code with enhanced syntax highlighting
        y_offset = 180
        for line in code.split('\n'):
            if not line.strip():
                y_offset += 60
                continue
                
            # Better syntax coloring
            if any(kw in line for kw in ['print', 'def', 'class', 'if', 'else', 'for', 'while', 'import', 'from', 'return']):
                color = '#ff6b9d'  # Hot pink for keywords
            elif '"' in line or "'" in line:
                color = '#4ade80'  # Bright green for strings
            elif any(c.isdigit() for c in line):
                color = '#fbbf24'  # Yellow for numbers
            else:
                color = '#e0e7ff'  # Light purple-white for others
            
            # Add code line with slight shadow
            card_draw.text((62, y_offset+2), line, fill=(0, 0, 0, 80), font=font_code)
            card_draw.text((60, y_offset), line, fill=color, font=font_code)
            y_offset += 62
        
        # Paste card onto image
        img.paste(card, (card_margin, card_margin), card)
        
        return img

    def create_video(self, day_data, audio_path, scheme):
        """Create STUNNING video with modern design"""
        from PIL import ImageDraw, ImageFont
        import numpy as np
        
        # Load audio to get duration first
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        # Create gradient background
        final_img = self.create_gradient_background(self.width, self.height, scheme['bg1'], scheme['bg2'])
        draw = ImageDraw.Draw(final_img)
        
        # Add decorative elements (floating particles)
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(2, 6)
            opacity = random.randint(30, 80)
            color = self.hex_to_rgb(scheme['accent']) + (opacity,)
            draw.ellipse([x, y, x+size, y+size], fill=color)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
        
        # Create title card with glassmorphism
        title_bg = Image.new('RGBA', (self.width-80, 200), (255, 255, 255, 30))
        title_draw = ImageDraw.Draw(title_bg)
        title_draw.rounded_rectangle([0, 0, self.width-80, 200], radius=30, 
                                     fill=self.hex_to_rgb(scheme['accent']) + (60,))
        
        # Draw title text with word wrap
        title_text = f"Day {day_data['day']}: {day_data['title']}"
        words = title_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = title_draw.textbbox((0, 0), test_line, font=title_font)
            if bbox[2] - bbox[0] < self.width - 180:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw title on card
        y_pos = 40
        for line in lines:
            bbox = title_draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x_pos = ((self.width-80) - text_width) // 2
            # Shadow
            title_draw.text((x_pos+4, y_pos+4), line, fill=(0, 0, 0, 150), font=title_font)
            # Main text
            title_draw.text((x_pos, y_pos), line, fill='#ffffff', font=title_font)
            y_pos += 75
        
        # Paste title card
        final_img.paste(title_bg, (40, 80), title_bg)
        
        # Create and paste code image with glow
        code_img = self.create_code_image(day_data['code'], day_data['day'], scheme)
        if code_img.mode != 'RGB':
            code_img = code_img.convert('RGB')
        
        # Resize and position code
        code_width = int(self.width * 0.92)
        aspect = code_img.height / code_img.width
        code_height = int(code_width * aspect)
        code_img_resized = code_img.resize((code_width, code_height))
        
        code_x = (self.width - code_width) // 2
        code_y = 350
        final_img.paste(code_img_resized, (code_x, code_y))
        
        # Create CTA with modern design
        cta_text = f"👍 LIKE & FOLLOW 🚀"
        cta_subtext = f"Day {day_data['day'] + 1} Coming Soon!"
        
        # CTA background with gradient
        cta_height = 180
        cta_y = self.height - cta_height - 50
        cta_bg = Image.new('RGBA', (self.width-60, cta_height), (255, 255, 255, 0))
        cta_draw = ImageDraw.Draw(cta_bg)
        
        # Draw CTA box with shadow
        shadow_offset = 6
        cta_draw.rounded_rectangle([shadow_offset, shadow_offset, self.width-60, cta_height], 
                                   radius=40, fill=(0, 0, 0, 80))
        cta_draw.rounded_rectangle([0, 0, self.width-60, cta_height], 
                                   radius=40, fill=self.hex_to_rgb(scheme['accent']))
        
        # Add pulsing border effect
        for i in range(3):
            cta_draw.rounded_rectangle([i*3, i*3, (self.width-60)-i*3, cta_height-i*3], 
                                       radius=40, outline='#ffffff', width=3)
        
        # Draw CTA text
        bbox = cta_draw.textbbox((0, 0), cta_text, font=cta_font)
        text_width = bbox[2] - bbox[0]
        text_x = ((self.width-60) - text_width) // 2
        
        # Shadow
        cta_draw.text((text_x+4, 35+4), cta_text, fill=(0, 0, 0, 150), font=cta_font)
        # Main text
        cta_draw.text((text_x, 35), cta_text, fill='#ffffff', font=cta_font)
        
        # Subtitle
        bbox2 = cta_draw.textbbox((0, 0), cta_subtext, font=subtitle_font)
        text_width2 = bbox2[2] - bbox2[0]
        text_x2 = ((self.width-60) - text_width2) // 2
        cta_draw.text((text_x2+3, 105+3), cta_subtext, fill=(0, 0, 0, 120), font=subtitle_font)
        cta_draw.text((text_x2, 105), cta_subtext, fill='#ffffff', font=subtitle_font)
        
        # Paste CTA
        final_img.paste(cta_bg, (30, cta_y), cta_bg)
        
        # Save the image
        img_path = self.output_folder / f"temp_full_{day_data['day']}.png"
        final_img.save(str(img_path))
        
        # Create video from image
        img_clip = ImageClip(str(img_path)).set_duration(duration).fadein(0.5).fadeout(0.5)
        
        # Add audio
        video = img_clip.set_audio(audio)
        
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
            script = self.generate_script(day_data)
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
            
            if (self.output_folder / f"temp_full_{day_data['day']}.png").exists():
                (self.output_folder / f"temp_full_{day_data['day']}.png").unlink()
            
            time.sleep(2)

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.create_all_videos("content.json", language="python")
    
    print("\n" + "="*50)
    print("✨ ALL VIDEOS GENERATED SUCCESSFULLY!")
    print("="*50)
    print(f"📁 Videos saved in: {automation.output_folder}")
    print("🚀 Ready for YouTube upload!")
