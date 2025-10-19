import json
import os
import requests
import time
from pathlib import Path
from moviepy.editor import (
    VideoClip, TextClip, CompositeVideoClip, 
    ColorClip, ImageClip, AudioFileClip, AudioClip, concatenate_videoclips
)
from moviepy.video.fx import fadein, fadeout, resize
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
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
        
        # Ultra vibrant color schemes
        self.color_schemes = [
            {"bg1": "#667eea", "bg2": "#764ba2", "accent": "#f093fb", "text": "#ffffff", "code_bg": "#2d1b4e", "shadow": "#4a148c", "particle": "#ffd700"},
            {"bg1": "#f093fb", "bg2": "#f5576c", "accent": "#ffd89b", "text": "#ffffff", "code_bg": "#5e2129", "shadow": "#c2185b", "particle": "#43e97b"},
            {"bg1": "#4facfe", "bg2": "#00f2fe", "accent": "#43e97b", "text": "#ffffff", "code_bg": "#1a3a52", "shadow": "#0277bd", "particle": "#ffd700"},
            {"bg1": "#fa709a", "bg2": "#fee140", "accent": "#30cfd0", "text": "#ffffff", "code_bg": "#5e2a0c", "shadow": "#d84315", "particle": "#a8edea"},
            {"bg1": "#30cfd0", "bg2": "#330867", "accent": "#a8edea", "text": "#ffffff", "code_bg": "#1a1033", "shadow": "#1a237e", "particle": "#ffd700"},
            {"bg1": "#ff6a00", "bg2": "#ee0979", "accent": "#ffd89b", "text": "#ffffff", "code_bg": "#4d0e2f", "shadow": "#b71c1c", "particle": "#43e97b"},
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
        """Convert text to speech using ElevenLabs with key rotation - SLOWER voice"""
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
                    "stability": 0.6,  # More stable
                    "similarity_boost": 0.8,  # More natural
                    "style": 0.3,  # Less dramatic
                    "use_speaker_boost": True  # Better clarity
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

    def create_animated_gradient(self, width, height, color1, color2, frame_count=90):
        """Create animated gradient frames"""
        frames = []
        for i in range(frame_count):
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            r1, g1, b1 = self.hex_to_rgb(color1)
            r2, g2, b2 = self.hex_to_rgb(color2)
            
            # Animated offset
            offset = int((i / frame_count) * height * 0.3)
            
            for y in range(height):
                ratio = ((y + offset) % height) / height
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            frames.append(np.array(img))
        
        return frames

    def create_particle_frame(self, width, height, scheme, progress):
        """Create animated particles for a frame"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        particle_color = self.hex_to_rgb(scheme['particle'])
        
        # 50 animated particles
        for i in range(50):
            seed = i * 123.456
            x = int((seed * 7 + progress * 100) % width)
            y = int((seed * 11 + progress * 50) % height)
            size = int(3 + (seed % 5))
            opacity = int(40 + (seed % 60))
            
            draw.ellipse([x, y, x+size, y+size], fill=particle_color + (opacity,))
        
        return img

    def create_glow_code_image(self, code, day, scheme, output_text=None):
        """Create code image with GLOW and optional output"""
        img = Image.new('RGB', (950, 800), self.hex_to_rgb(scheme['code_bg']))
        draw = ImageDraw.Draw(img)
        
        # Animated glow effect
        glow_layer = Image.new('RGBA', (950, 800), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        
        # Pulsing glow rectangles
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        for i in range(10, 50, 10):
            opacity = max(0, 100 - i*2)
            glow_draw.rectangle([25-i, 25-i, 925+i, 775+i], 
                               outline=accent_rgb + (opacity,), width=5)
        
        img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
        
        # Glassmorphism card
        card = Image.new('RGBA', (900, 750), self.hex_to_rgb(scheme['code_bg']) + (230,))
        card_draw = ImageDraw.Draw(card)
        
        # Neon border
        border_color = self.hex_to_rgb(scheme['accent'])
        for i in range(8):
            card_draw.rounded_rectangle(
                [i*2, i*2, 900-i*2, 750-i*2], 
                radius=30, 
                outline=border_color + (150 - i*15,),
                width=3
            )
        
        try:
            font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 44)
            font_day = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
            font_output = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 40)
        except:
            font_code = ImageFont.load_default()
            font_day = ImageFont.load_default()
            font_output = ImageFont.load_default()
        
        # Day badge with GLOW
        badge_x, badge_y = 40, 35
        badge_w, badge_h = 200, 100
        
        # Glow layers
        for offset in range(12, 0, -3):
            alpha = max(0, 120 - offset*10)
            card_draw.rounded_rectangle(
                [badge_x-offset, badge_y-offset, 
                 badge_x+badge_w+offset, badge_y+badge_h+offset],
                radius=25, fill=self.hex_to_rgb(scheme['accent']) + (alpha,)
            )
        
        # Main badge
        card_draw.rounded_rectangle(
            [badge_x, badge_y, badge_x+badge_w, badge_y+badge_h], 
            radius=25, fill=self.hex_to_rgb(scheme['accent'])
        )
        
        # Badge text with glow
        day_text = f"DAY {day}"
        bbox = card_draw.textbbox((0, 0), day_text, font=font_day)
        text_w = bbox[2] - bbox[0]
        text_x = badge_x + (badge_w - text_w) // 2
        text_y = badge_y + 22
        
        # Text glow
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2), (3,3)]:
            card_draw.text((text_x+offset[0], text_y+offset[1]), day_text, 
                          fill=(255, 255, 255, 80), font=font_day)
        card_draw.text((text_x, text_y), day_text, fill='#ffffff', font=font_day)
        
        # Code with NEON syntax highlighting
        y_offset = 170
        for line in code.split('\n'):
            if not line.strip():
                y_offset += 65
                continue
            
            # Ultra vibrant colors
            if any(kw in line for kw in ['print', 'def', 'class', 'if', 'else', 'for', 'while', 'import', 'from', 'return']):
                color = '#ff3e9d'  # Hot neon pink
            elif '"' in line or "'" in line:
                color = '#00ff88'  # Neon green
            elif any(c.isdigit() for c in line):
                color = '#ffff00'  # Bright yellow
            else:
                color = '#ffffff'  # White
            
            # Glow effect on code
            for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
                card_draw.text((62+offset[0], y_offset+offset[1]), line, 
                              fill=(self.hex_to_rgb(color) + (50,)), font=font_code)
            card_draw.text((60, y_offset), line, fill=color, font=font_code)
            y_offset += 65
        
        # OUTPUT section with highlight
        if output_text:
            y_offset += 30
            
            # Output box with glow
            output_box_y = y_offset - 20
            output_box_h = 120
            
            # Glowing output background
            for offset in range(8, 0, -2):
                alpha = 80 - offset*10
                card_draw.rounded_rectangle(
                    [40-offset, output_box_y-offset, 860+offset, output_box_y+output_box_h+offset],
                    radius=20, fill=self.hex_to_rgb('#00ff88') + (alpha,)
                )
            
            card_draw.rounded_rectangle(
                [40, output_box_y, 860, output_box_y+output_box_h],
                radius=20, fill=(0, 40, 20, 200)
            )
            
            # "OUTPUT:" label with glow
            output_label = "▶ OUTPUT:"
            card_draw.text((52, y_offset+2), output_label, fill=(0, 0, 0, 100), font=font_output)
            card_draw.text((50, y_offset), output_label, fill='#00ff88', font=font_output)
            
            # Actual output with glow
            y_offset += 55
            for offset in [(2,2), (-2,2)]:
                card_draw.text((52+offset[0], y_offset+offset[1]), output_text, 
                              fill=(255, 255, 255, 60), font=font_output)
            card_draw.text((50, y_offset), output_text, fill='#ffffff', font=font_output)
        
        # Paste card
        img.paste(card, (25, 25), card)
        
        return img

    def create_video(self, day_data, audio_path, scheme):
        """Create STUNNING animated video with OUTPUT"""
        # Get audio duration
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        # Detect if code has output
        code = day_data['code']
        output_text = None
        if 'print' in code.lower():
            # Extract what's being printed
            if "print('Hello, World!')" in code:
                output_text = "Hello, World!"
            elif "print" in code:
                # Simple extraction
                try:
                    if "'" in code or '"' in code:
                        parts = code.split('print(')[1].split(')')[0]
                        output_text = parts.strip('\'"')[:50]
                except:
                    output_text = "Output appears here"
        
        # Split duration: intro + code + output
        intro_duration = min(2, duration * 0.15)
        code_duration = duration - intro_duration
        
        # FRAME 1: Animated intro with gradient
        print("Creating intro frame...")
        gradient_frames = self.create_animated_gradient(self.width, self.height, 
                                                        scheme['bg1'], scheme['bg2'], 
                                                        frame_count=int(self.fps * intro_duration))
        
        intro_img = Image.new('RGB', (self.width, self.height))
        intro_draw = ImageDraw.Draw(intro_img)
        
        try:
            huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except:
            huge_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Create intro frames with particles
        intro_frames = []
        for i, grad_frame in enumerate(gradient_frames):
            frame_img = Image.fromarray(grad_frame)
            frame_draw = ImageDraw.Draw(frame_img)
            
            # Add particles
            particles = self.create_particle_frame(self.width, self.height, scheme, i/len(gradient_frames))
            frame_img.paste(particles, (0, 0), particles)
            
            # Day number with MASSIVE glow
            day_text = f"DAY {day_data['day']}"
            bbox = frame_draw.textbbox((0, 0), day_text, font=huge_font)
            text_w = bbox[2] - bbox[0]
            text_x = (self.width - text_w) // 2
            text_y = self.height // 2 - 100
            
            # Glow
            for offset in range(20, 0, -4):
                alpha = max(0, 200 - offset*10)
                frame_draw.text((text_x, text_y), day_text, 
                              fill=self.hex_to_rgb(scheme['accent']) + (alpha,), 
                              font=huge_font)
            frame_draw.text((text_x, text_y), day_text, fill='#ffffff', font=huge_font)
            
            # Title
            title_text = day_data['title']
            bbox2 = frame_draw.textbbox((0, 0), title_text, font=title_font)
            text_w2 = bbox2[2] - bbox2[0]
            text_x2 = (self.width - text_w2) // 2
            text_y2 = self.height // 2 + 50
            
            frame_draw.text((text_x2+3, text_y2+3), title_text, fill=(0, 0, 0, 150), font=title_font)
            frame_draw.text((text_x2, text_y2), title_text, fill='#ffffff', font=title_font)
            
            intro_frames.append(np.array(frame_img))
        
        # Create intro clip
        intro_clip = ImageClip(intro_frames[0]).set_duration(intro_duration)
        intro_clip = intro_clip.fl(lambda gf, t: intro_frames[min(int(t*self.fps), len(intro_frames)-1)])
        
        # FRAME 2: Code with gradient background + particles + OUTPUT
        print("Creating main code frame...")
        main_bg = self.create_animated_gradient(self.width, self.height, 
                                                scheme['bg1'], scheme['bg2'], 
                                                frame_count=1)[0]
        main_img = Image.fromarray(main_bg)
        
        # Add particles
        particles = self.create_particle_frame(self.width, self.height, scheme, 0.5)
        main_img.paste(particles, (0, 0), particles)
        
        # Title card
        title_bg = Image.new('RGBA', (self.width-80, 180), (255, 255, 255, 0))
        title_draw = ImageDraw.Draw(title_bg)
        
        # Glow
        for i in range(15, 0, -3):
            alpha = 80 - i*5
            title_draw.rounded_rectangle([0-i, 0-i, self.width-80+i, 180+i], radius=40, 
                                         fill=self.hex_to_rgb(scheme['accent']) + (alpha,))
        
        title_draw.rounded_rectangle([0, 0, self.width-80, 180], radius=40, 
                                     fill=self.hex_to_rgb(scheme['accent']) + (120,))
        
        try:
            main_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        except:
            main_title_font = ImageFont.load_default()
        
        # Title text
        title_full = f"Day {day_data['day']}: {day_data['title']}"
        bbox = title_draw.textbbox((0, 0), title_full, font=main_title_font)
        title_w = bbox[2] - bbox[0]
        
        if title_w > self.width - 160:
            # Word wrap
            words = title_full.split()
            line1 = []
            line2 = []
            for word in words:
                test = ' '.join(line1 + [word])
                bbox = title_draw.textbbox((0, 0), test, font=main_title_font)
                if bbox[2] - bbox[0] < self.width - 160:
                    line1.append(word)
                else:
                    line2.append(word)
            
            y = 35
            for line in [' '.join(line1), ' '.join(line2)]:
                bbox = title_draw.textbbox((0, 0), line, font=main_title_font)
                x = ((self.width-80) - (bbox[2] - bbox[0])) // 2
                title_draw.text((x+4, y+4), line, fill=(0, 0, 0, 150), font=main_title_font)
                title_draw.text((x, y), line, fill='#ffffff', font=main_title_font)
                y += 75
        else:
            title_x = ((self.width-80) - title_w) // 2
            title_draw.text((title_x+4, 54), title_full, fill=(0, 0, 0, 150), font=main_title_font)
            title_draw.text((title_x, 50), title_full, fill='#ffffff', font=main_title_font)
        
        main_img.paste(title_bg, (40, 100), title_bg)
        
        # Code with OUTPUT
        code_img = self.create_glow_code_image(code, day_data['day'], scheme, output_text)
        code_resized = code_img.resize((int(self.width * 0.92), int(800 * (self.width * 0.92) / 950)))
        
        code_x = (self.width - code_resized.width) // 2
        code_y = 320
        main_img.paste(code_resized, (code_x, code_y))
        
        # CTA
        cta_bg = Image.new('RGBA', (self.width-60, 200), (255, 255, 255, 0))
        cta_draw = ImageDraw.Draw(cta_bg)
        
        # Pulsing glow
        for i in range(20, 0, -4):
            alpha = 100 - i*5
            cta_draw.rounded_rectangle([0-i, 0-i, self.width-60+i, 200+i], radius=50,
                                       fill=self.hex_to_rgb(scheme['accent']) + (alpha,))
        
        cta_draw.rounded_rectangle([0, 0, self.width-60, 200], radius=50,
                                   fill=self.hex_to_rgb(scheme['accent']))
        
        # Triple border
        for i in range(3):
            cta_draw.rounded_rectangle([i*4, i*4, (self.width-60)-i*4, 200-i*4], 
                                       radius=50, outline='#ffffff', width=4)
        
        try:
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
            sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        except:
            cta_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
        
        cta_text = "👍 SMASH THAT LIKE! 🚀"
        bbox = cta_draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_x = ((self.width-60) - (bbox[2] - bbox[0])) // 2
        cta_draw.text((cta_x+4, 44), cta_text, fill=(0, 0, 0, 150), font=cta_font)
        cta_draw.text((cta_x, 40), cta_text, fill='#ffffff', font=cta_font)
        
        sub_text = f"Day {day_data['day'] + 1} drops TOMORROW!"
        bbox2 = cta_draw.textbbox((0, 0), sub_text, font=sub_font)
        sub_x = ((self.width-60) - (bbox2[2] - bbox2[0])) // 2
        cta_draw.text((sub_x+3, 123), sub_text, fill=(0, 0, 0, 120), font=sub_font)
        cta_draw.text((sub_x, 120), sub_text, fill='#ffffff', font=sub_font)
        
        main_img.paste(cta_bg, (30, self.height-270), cta_bg)
        
        # Save
        main_path = self.output_folder / f"temp_main_{day_data['day']}.png"
        main_img.save(str(main_path))
        
        # Create main clip
        main_clip = ImageClip(str(main_path)).set_duration(code_duration).fadein(0.5).fadeout(0.5)
        
        # Combine clips
        final_video = concatenate_videoclips([intro_clip, main_clip])
        final_video = final_video.set_audio(audio)
        
        return final_video

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
            
            print("🎬 Creating animated video...")
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
            
            # Cleanup temp files
            temp_files = [
                self.output_folder / f"temp_full_{day_data['day']}.png",
                self.output_folder / f"temp_main_{day_data['day']}.png",
            ]
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            
            time.sleep(2)

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.create_all_videos("content.json", language="python")
    
    print("\n" + "="*50)
    print("✨ ALL VIDEOS GENERATED SUCCESSFULLY!")
    print("="*50)
    print(f"📁 Videos saved in: {automation.output_folder}")
    print("🚀 Ready for YouTube upload!")
