import json
import os
import requests
import time
from pathlib import Path
from moviepy.editor import (
    VideoClip, CompositeVideoClip, 
    ColorClip, ImageClip, AudioFileClip, AudioClip, concatenate_videoclips
)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import urllib.request

class YouTubeAutomation:
    def __init__(self):
        self.elevenlabs_keys = [
            os.getenv('ELEVENLABS_KEY_1'),
            os.getenv('ELEVENLABS_KEY_2'),
            os.getenv('ELEVENLABS_KEY_3')
        ]
        self.current_key_index = 0
        
        self.output_folder = Path("output")
        self.output_folder.mkdir(exist_ok=True)
        
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
        # Ultra-modern color schemes
        self.color_schemes = [
            {"name": "matrix", "bg1": "#001f0f", "bg2": "#003820", "accent": "#00ff41", "text": "#ffffff", "glass": (0, 255, 65, 30)},
            {"name": "cyber", "bg1": "#0a0e27", "bg2": "#1a1f4f", "accent": "#00d9ff", "text": "#ffffff", "glass": (0, 217, 255, 30)},
            {"name": "neon", "bg1": "#1a0033", "bg2": "#330066", "accent": "#ff00ff", "text": "#ffffff", "glass": (255, 0, 255, 30)},
            {"name": "sunset", "bg1": "#1a0a00", "bg2": "#4d1f00", "accent": "#ff6600", "text": "#ffffff", "glass": (255, 102, 0, 30)},
            {"name": "ice", "bg1": "#001a33", "bg2": "#003366", "accent": "#00ffff", "text": "#ffffff", "glass": (0, 255, 255, 30)},
        ]

    def load_content(self, json_path="content.json"):
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data['days']

    def generate_script(self, day_data):
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
        ]
        return random.choice(scripts)

    def _explain_code(self, code, title):
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
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        for attempt in range(len(self.elevenlabs_keys)):
            api_key = self.elevenlabs_keys[self.current_key_index]
            
            if not api_key:
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
                    "stability": 0.6,
                    "similarity_boost": 0.8,
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
                    self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
                else:
                    return False
            except Exception as e:
                self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
        
        return False

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def create_matrix_rain(self, width, height, scheme, frame_count=90):
        """Create Matrix-style falling code animation"""
        frames = []
        num_cols = 40
        col_width = width // num_cols
        
        # Initialize columns with random positions
        cols = [random.randint(-height, 0) for _ in range(num_cols)]
        
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        
        for frame in range(frame_count):
            img = Image.new('RGB', (width, height), self.hex_to_rgb(scheme['bg1']))
            draw = ImageDraw.Draw(img)
            
            # Update and draw each column
            for i, y_pos in enumerate(cols):
                x = i * col_width + col_width // 2
                
                # Draw trail
                for j in range(20):
                    y = y_pos - j * 30
                    if 0 <= y < height:
                        opacity = max(0, 255 - j * 12)
                        size = max(2, 8 - j // 3)
                        color = tuple([int(c * opacity / 255) for c in accent_rgb])
                        draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
                
                # Move column down
                cols[i] += random.randint(15, 30)
                if cols[i] > height:
                    cols[i] = -random.randint(100, 300)
            
            frames.append(np.array(img))
        
        return frames

    def create_circuit_board(self, width, height, scheme, frame_count=90):
        """Create animated circuit board background"""
        frames = []
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        
        # Generate circuit paths
        num_paths = 30
        paths = []
        for _ in range(num_paths):
            points = []
            x, y = random.randint(0, width), random.randint(0, height)
            for _ in range(random.randint(3, 8)):
                points.append((x, y))
                x += random.choice([-1, 0, 1]) * random.randint(50, 200)
                y += random.choice([-1, 0, 1]) * random.randint(50, 200)
                x = max(0, min(width, x))
                y = max(0, min(height, y))
            paths.append(points)
        
        for frame in range(frame_count):
            img = Image.new('RGB', (width, height), self.hex_to_rgb(scheme['bg1']))
            draw = ImageDraw.Draw(img)
            
            # Draw grid
            grid_spacing = 80
            for x in range(0, width, grid_spacing):
                for y in range(0, height, grid_spacing):
                    opacity = int(20 + 10 * np.sin(frame * 0.1 + x * 0.01))
                    draw.rectangle([x, y, x+2, y+2], fill=accent_rgb + (opacity,))
            
            # Draw paths with animation
            for path in paths:
                for i in range(len(path) - 1):
                    progress = (frame + i * 5) % frame_count / frame_count
                    opacity = int(150 * abs(np.sin(progress * np.pi)))
                    color = tuple([int(c * opacity / 255) for c in accent_rgb])
                    draw.line([path[i], path[i+1]], fill=color, width=3)
            
            # Add glowing nodes
            pulse = abs(np.sin(frame * 0.15))
            for path in paths:
                for point in path[::2]:
                    size = int(8 + 6 * pulse)
                    for offset in range(size, 0, -2):
                        alpha = int(100 * (1 - offset / size))
                        color = tuple([int(c * alpha / 255) for c in accent_rgb])
                        draw.ellipse([point[0]-offset, point[1]-offset, 
                                     point[0]+offset, point[1]+offset], fill=color)
            
            frames.append(np.array(img))
        
        return frames

    def create_glassmorphism_card(self, width, height, scheme, blur_amount=20):
        """Create glassmorphism effect card"""
        card = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        
        # Base glass layer
        glass_overlay = Image.new('RGBA', (width, height), scheme['glass'])
        card = Image.alpha_composite(card, glass_overlay)
        
        # Border glow
        draw = ImageDraw.Draw(card)
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        
        for i in range(10, 0, -2):
            alpha = int(80 - i * 8)
            draw.rounded_rectangle([i, i, width-i, height-i], radius=25, 
                                   outline=accent_rgb + (alpha,), width=3)
        
        # Apply blur for glass effect
        card = card.filter(ImageFilter.GaussianBlur(5))
        
        return card

    def get_emoji_image(self, emoji_char):
        """Get emoji as image (fallback to text)"""
        # For now, we'll use text rendering with better fallback
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a font that supports emojis
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 70)
        except:
            font = ImageFont.load_default()
        
        # Draw emoji
        bbox = draw.textbbox((0, 0), emoji_char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (100 - text_width) // 2
        y = (100 - text_height) // 2
        
        draw.text((x, y), emoji_char, font=font, fill=(255, 255, 255, 255))
        
        return img

    def create_code_card(self, code, day, scheme, output_text=None):
        """Create modern code card with glassmorphism"""
        # Calculate dynamic height based on content
        base_height = 700
        if output_text:
            base_height += 150
        
        lines = code.split('\n')
        line_height = 65
        code_height = len(lines) * line_height + 200
        
        card_height = max(base_height, code_height)
        card_width = 950
        
        # Create card with glassmorphism
        card = self.create_glassmorphism_card(card_width, card_height, scheme)
        draw = ImageDraw.Draw(card)
        
        try:
            font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 42)
            font_day = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_output = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 38)
        except:
            font_code = ImageFont.load_default()
            font_day = ImageFont.load_default()
            font_output = ImageFont.load_default()
        
        # Day badge with parallax effect
        badge_w, badge_h = 180, 90
        badge_x, badge_y = 40, 35
        
        # Create badge with glow
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        for offset in range(12, 0, -3):
            alpha = max(0, 150 - offset * 12)
            draw.rounded_rectangle(
                [badge_x-offset, badge_y-offset, badge_x+badge_w+offset, badge_y+badge_h+offset],
                radius=25, fill=accent_rgb + (alpha,)
            )
        
        draw.rounded_rectangle([badge_x, badge_y, badge_x+badge_w, badge_y+badge_h], 
                              radius=25, fill=accent_rgb + (255,))
        
        # Day text
        day_text = f"DAY {day}"
        bbox = draw.textbbox((0, 0), day_text, font=font_day)
        text_w = bbox[2] - bbox[0]
        text_x = badge_x + (badge_w - text_w) // 2
        draw.text((text_x, badge_y + 20), day_text, fill='#ffffff', font=font_day)
        
        # Code with neon syntax highlighting
        y_offset = 160
        for line in lines:
            if not line.strip():
                y_offset += line_height
                continue
            
            # Neon colors
            if any(kw in line for kw in ['print', 'def', 'class', 'if', 'else', 'for', 'while', 'import', 'return']):
                color = '#ff3e9d'
            elif '"' in line or "'" in line:
                color = '#00ff88'
            elif any(c.isdigit() for c in line):
                color = '#ffff00'
            else:
                color = '#ffffff'
            
            # Glow effect
            glow_rgb = self.hex_to_rgb(color)
            for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
                draw.text((60+offset[0], y_offset+offset[1]), line, 
                         fill=glow_rgb + (60,), font=font_code)
            draw.text((60, y_offset), line, fill=color, font=font_code)
            y_offset += line_height
        
        # OUTPUT section with glow
        if output_text:
            y_offset += 40
            output_box_h = 130
            
            # Glowing output box
            for offset in range(10, 0, -2):
                alpha = 100 - offset * 10
                draw.rounded_rectangle(
                    [35-offset, y_offset-offset, card_width-35+offset, y_offset+output_box_h+offset],
                    radius=20, fill=self.hex_to_rgb('#00ff88') + (alpha,)
                )
            
            draw.rounded_rectangle(
                [35, y_offset, card_width-35, y_offset+output_box_h],
                radius=20, fill=(0, 50, 25, 200)
            )
            
            # OUTPUT label with emoji
            output_emoji = self.get_emoji_image("▶")
            card.paste(output_emoji, (50, y_offset + 10), output_emoji)
            
            draw.text((160, y_offset + 15), "OUTPUT:", fill='#00ff88', font=font_output)
            draw.text((160, y_offset + 65), output_text, fill='#ffffff', font=font_output)
        
        return card

    def create_video(self, day_data, audio_path, scheme):
        """Create ULTRA-MODERN animated video"""
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        # Detect output
        code = day_data['code']
        output_text = None
        if 'print' in code.lower():
            if "print('Hello, World!')" in code:
                output_text = "Hello, World!"
            elif "print" in code:
                try:
                    parts = code.split('print(')[1].split(')')[0]
                    output_text = parts.strip('\'"')[:40]
                except:
                    output_text = "Output here"
        
        # Create animated background
        print(f"Creating {scheme['name']} background animation...")
        if scheme['name'] in ['matrix', 'cyber', 'ice']:
            bg_frames = self.create_matrix_rain(self.width, self.height, scheme, frame_count=int(self.fps * duration))
        else:
            bg_frames = self.create_circuit_board(self.width, self.height, scheme, frame_count=int(self.fps * duration))
        
        # Create content layers
        print("Creating glassmorphism content...")
        
        # Title card
        title_card = self.create_glassmorphism_card(self.width - 80, 200, scheme)
        title_draw = ImageDraw.Draw(title_card)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        except:
            title_font = ImageFont.load_default()
        
        title_text = f"Day {day_data['day']}: {day_data['title']}"
        
        # Word wrap
        words = title_text.split()
        lines = []
        current_line = []
        for word in words:
            test = ' '.join(current_line + [word])
            bbox = title_draw.textbbox((0, 0), test, font=title_font)
            if bbox[2] - bbox[0] < (self.width - 180):
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        y = 45
        for line in lines:
            bbox = title_draw.textbbox((0, 0), line, font=title_font)
            x = ((self.width - 80) - (bbox[2] - bbox[0])) // 2
            # Glow
            glow_color = self.hex_to_rgb(scheme['accent'])
            for offset in [(3,3), (-3,3), (3,-3), (-3,-3)]:
                title_draw.text((x+offset[0], y+offset[1]), line, 
                              fill=glow_color + (80,), font=title_font)
            title_draw.text((x, y), line, fill='#ffffff', font=title_font)
            y += 75
        
        # Code card
        code_card = self.create_code_card(code, day_data['day'], scheme, output_text)
        
        # CTA card
        cta_card = self.create_glassmorphism_card(self.width - 60, 220, scheme)
        cta_draw = ImageDraw.Draw(cta_card)
        
        try:
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
            sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            cta_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
        
        # Add emoji images
        like_emoji = self.get_emoji_image("👍")
        rocket_emoji = self.get_emoji_image("🚀")
        
        cta_text = "  LIKE & FOLLOW  "
        bbox = cta_draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_x = ((self.width - 60) - (bbox[2] - bbox[0]) - 200) // 2
        
        # Place emojis
        cta_card.paste(like_emoji, (cta_x, 40), like_emoji)
        cta_card.paste(rocket_emoji, (cta_x + (bbox[2]-bbox[0]) + 100, 40), rocket_emoji)
        
        cta_draw.text((cta_x + 110, 50), cta_text, fill='#ffffff', font=cta_font)
        
        sub_text = f"Day {day_data['day'] + 1} Coming Soon!"
        bbox2 = cta_draw.textbbox((0, 0), sub_text, font=sub_font)
        sub_x = ((self.width - 60) - (bbox2[2] - bbox2[0])) // 2
        cta_draw.text((sub_x, 140), sub_text, fill=self.hex_to_rgb(scheme['accent']), font=sub_font)
        
        # Composite frames
        print("Compositing animated frames...")
        final_frames = []
        
        for i, bg_frame in enumerate(bg_frames):
            frame_img = Image.fromarray(bg_frame)
            
            # Add gradient overlay
            gradient = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 100))
            frame_img = Image.alpha_composite(frame_img.convert('RGBA'), gradient).convert('RGB')
            
            # Parallax effect - slight movement
            offset_x = int(10 * np.sin(i * 0.05))
            offset_y = int(5 * np.cos(i * 0.05))
            
            # Paste title card with parallax
            frame_img.paste(title_card, (40 + offset_x, 120 + offset_y), title_card)
            
            # Paste code card
            code_y = 380
            code_resized = code_card.resize((int(self.width * 0.92), 
                                            int(code_card.height * (self.width * 0.92) / code_card.width)))
            code_x = (self.width - code_resized.width) // 2
            frame_img.paste(code_resized, (code_x - offset_x, code_y + offset_y // 2), code_resized)
            
            # Paste CTA
            frame_img.paste(cta_card, (30 + offset_x, self.height - 280 - offset_y), cta_card)
            
            final_frames.append(np.array(frame_img))
        
        # Save first frame and create clip
        first_frame_path = self.output_folder / f"temp_video_{day_data['day']}.png"
        Image.fromarray(final_frames[0]).save(str(first_frame_path))
        
        # Create video with animation
        def make_frame(t):
            frame_idx = int(t * self.fps) % len(final_frames)
            return final_frames[frame_idx]
        
        video_clip = VideoClip(make_frame, duration=duration)
        video_clip = video_clip.set_audio(audio)
        
        return video_clip

    def generate_youtube_metadata(self, day_data):
        title = f"Day {day_data['day']}: {day_data['title']} | Python Tutorial #shorts #viral #programming"
        
        description = f"""🔥 Day {day_data['day']} of our 30-Day Coding Challenge! 

Today's Topic: {day_data['title']}

Code:
{day_data['code']}

💡 Master this concept and level up your programming skills!

👉 Follow for Day {day_data['day'] + 1}!

#python #coding #programming #shorts #viral #codingtutorial #pythonforbeginners 
#learnpython #pythonprogramming #codingshorts #programmingshorts #techeducation

⏰ 30 Days of Python - Don't miss a day!
📚 Perfect for beginners and intermediate programmers
🚀 Quick, easy-to-understand explanations

Subscribe and turn on notifications! 🔔"""

        tags = [
            "python", "programming", "coding", "tutorial", "shorts",
            "python tutorial", "learn python", "coding for beginners",
            "python programming", "software development", "tech education",
        ]
        
        return {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "category": "27",
            "privacyStatus": "public"
        }

    def create_all_videos(self, json_path="content.json", language="python"):
        days = self.load_content(json_path)
        
        for day_data in days:
            print(f"\n{'='*50}")
            print(f"Processing Day {day_data['day']}: {day_data['title']}")
            print(f"{'='*50}")
            
            scheme = random.choice(self.color_schemes)
            script = self.generate_script(day_data)
            
            audio_path = self.output_folder / f"day_{day_data['day']}_audio.mp3"
            if not self.text_to_speech_elevenlabs(script, str(audio_path)):
                silent = AudioClip(lambda t: 0, duration=5, fps=44100)
                silent.write_audiofile(str(audio_path))
            
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
            
            metadata = self.generate_youtube_metadata(day_data)
            metadata_path = self.output_folder / f"day_{day_data['day']}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Cleanup temp files
            for temp_file in self.output_folder.glob(f"temp_*_{day_data['day']}.*"):
                temp_file.unlink()
            
            time.sleep(2)

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.create_all_videos("content.json", language="python")
    
    print("\n✨ ALL VIDEOS GENERATED!")
    print(f"📁 Videos in: {automation.output_folder}")
