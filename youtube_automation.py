import json
import os
import requests
import time
from pathlib import Path
from moviepy.editor import VideoClip, AudioFileClip, AudioClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import subprocess
import sys

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
        
        # Modern color schemes with better accent colors
        self.color_schemes = [
            {"name": "matrix", "bg1": "#001a0f", "bg2": "#003d20", "accent": "#00ff41", "text": "#ffffff", "badge": "#00ff41"},
            {"name": "cyber", "bg1": "#0a0e27", "bg2": "#1a1f4f", "accent": "#00d9ff", "text": "#ffffff", "badge": "#7b2ff7"},
            {"name": "neon", "bg1": "#1a0033", "bg2": "#330066", "accent": "#ff00ff", "text": "#ffffff", "badge": "#ff0080"},
            {"name": "sunset", "bg1": "#1a0a00", "bg2": "#4d1f00", "accent": "#ff6600", "text": "#ffffff", "badge": "#ff3300"},
            {"name": "ice", "bg1": "#001a33", "bg2": "#003366", "accent": "#00ffff", "text": "#ffffff", "badge": "#0099ff"},
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
                    print(f"✓ Audio generated")
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

    def execute_python_code(self, code):
        """Execute Python code and capture output"""
        try:
            # Create a temporary file
            temp_file = self.output_folder / "temp_exec.py"
            with open(temp_file, 'w') as f:
                f.write(code)
            
            # Execute and capture output
            result = subprocess.run(
                [sys.executable, str(temp_file)],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Cleanup
            temp_file.unlink()
            
            # Return output
            output = result.stdout.strip()
            if output:
                return output[:100]  # Limit length
            return None
            
        except Exception as e:
            return None

    def create_gradient_bg(self, width, height, color1, color2):
        """Create smooth gradient background"""
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

    def create_glassmorphism_card(self, width, height, scheme):
        """Create glassmorphism card"""
        card = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        
        # Glass layer
        glass = Image.new('RGBA', (width, height), (255, 255, 255, 25))
        card = Image.alpha_composite(card, glass)
        
        # Border glow
        draw = ImageDraw.Draw(card)
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        
        for i in range(8, 0, -2):
            alpha = int(100 - i * 10)
            draw.rounded_rectangle([i, i, width-i, height-i], radius=25, 
                                   outline=accent_rgb + (alpha,), width=3)
        
        card = card.filter(ImageFilter.GaussianBlur(3))
        
        return card

    def draw_text_with_glow(self, draw, pos, text, font, color, glow_color=None):
        """Draw text with glow effect"""
        if glow_color is None:
            glow_color = color
        
        glow_rgb = self.hex_to_rgb(glow_color) if isinstance(glow_color, str) else glow_color
        
        # Glow
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2), (3,3), (-3,-3)]:
            draw.text((pos[0]+offset[0], pos[1]+offset[1]), text, 
                     fill=glow_rgb + (60,), font=font)
        
        # Main text
        draw.text(pos, text, fill=color, font=font)

    def create_video_frame(self, scheme, day, title, code_lines, output_text, 
                          code_progress, output_progress, show_output):
        """Create a single video frame with typing animation"""
        
        # Gradient background
        frame = self.create_gradient_bg(self.width, self.height, scheme['bg1'], scheme['bg2'])
        
        # Add subtle grid pattern
        draw = ImageDraw.Draw(frame)
        grid_color = self.hex_to_rgb(scheme['accent'])
        for x in range(0, self.width, 100):
            for y in range(0, self.height, 100):
                draw.rectangle([x, y, x+1, y+1], fill=grid_color + (20,))
        
        # Title card
        title_card = self.create_glassmorphism_card(self.width - 80, 180, scheme)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
            code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)
            day_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
            output_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 36)
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        except:
            title_font = ImageFont.load_default()
            code_font = ImageFont.load_default()
            day_font = ImageFont.load_default()
            output_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
        
        # Draw title on card
        title_draw = ImageDraw.Draw(title_card)
        full_title = f"Day {day}: {title}"
        
        # Word wrap
        words = full_title.split()
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
        
        y = 40
        for line in lines:
            bbox = title_draw.textbbox((0, 0), line, font=title_font)
            x = ((self.width - 80) - (bbox[2] - bbox[0])) // 2
            self.draw_text_with_glow(title_draw, (x, y), line, title_font, '#ffffff', scheme['accent'])
            y += 70
        
        frame.paste(title_card, (40, 100), title_card)
        
        # Code card with dynamic height
        num_lines = len(code_lines)
        card_height = 250 + num_lines * 60
        if show_output and output_text:
            card_height += 180
        
        code_card = self.create_glassmorphism_card(int(self.width * 0.92), card_height, scheme)
        code_draw = ImageDraw.Draw(code_card)
        
        # Day badge with animated border - BIGGER SIZE
        badge_w, badge_h = 220, 95
        badge_x, badge_y = 35, 30
        badge_rgb = self.hex_to_rgb(scheme['badge'])
        
        # Animated pulsing glow (use frame number for animation)
        pulse_value = len(code_progress) if code_progress else 0
        pulse = abs(np.sin(pulse_value * 0.2) * 0.3) + 0.7
        for offset in range(15, 0, -2):
            alpha = int(150 * pulse - offset * 10)
            code_draw.rounded_rectangle(
                [badge_x-offset, badge_y-offset, badge_x+badge_w+offset, badge_y+badge_h+offset],
                radius=25, fill=badge_rgb + (max(0, alpha),)
            )
        
        # Main badge
        code_draw.rounded_rectangle([badge_x, badge_y, badge_x+badge_w, badge_y+badge_h], 
                                    radius=25, fill=badge_rgb)
        
        # Animated border
        border_offset = int(3 * pulse)
        code_draw.rounded_rectangle(
            [badge_x+border_offset, badge_y+border_offset, 
             badge_x+badge_w-border_offset, badge_y+badge_h-border_offset],
            radius=25, outline=(255, 255, 255, 200), width=3
        )
        
        # Day text - WHITE color
        day_text = f"DAY {day}"
        bbox = code_draw.textbbox((0, 0), day_text, font=day_font)
        text_w = bbox[2] - bbox[0]
        text_x = badge_x + (badge_w - text_w) // 2
        # Glow effect on text
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
            code_draw.text((text_x+offset[0], badge_y+18+offset[1]), day_text, fill=(255, 255, 255, 100), font=day_font)
        code_draw.text((text_x, badge_y + 18), day_text, fill='#ffffff', font=day_font)
        
        # Typing animation for code
        y_offset = 150
        for i, line in enumerate(code_lines):
            if i < len(code_progress):
                displayed_line = code_progress[i]
            else:
                break
            
            if not displayed_line.strip():
                y_offset += 60
                continue
            
            # Syntax coloring
            if any(kw in displayed_line for kw in ['print', 'def', 'class', 'if', 'else', 'for', 'while', 'import', 'return']):
                color = '#ff3e9d'
            elif '"' in displayed_line or "'" in displayed_line:
                color = '#00ff88'
            elif any(c.isdigit() for c in displayed_line):
                color = '#ffff00'
            else:
                color = '#ffffff'
            
            self.draw_text_with_glow(code_draw, (55, y_offset), displayed_line, code_font, color, color)
            y_offset += 60
        
        # Cursor blinking effect
        if code_progress and len(code_progress[-1]) < len(code_lines[len(code_progress)-1]):
            cursor_y = 150 + (len(code_progress) - 1) * 60
            cursor_x = 55 + code_draw.textbbox((0, 0), code_progress[-1], font=code_font)[2]
            code_draw.rectangle([cursor_x, cursor_y, cursor_x+3, cursor_y+45], fill='#ffffff')
        
        # OUTPUT section with typing animation
        if show_output and output_text:
            y_offset += 35
            
            # Output box
            for offset in range(8, 0, -2):
                alpha = 80 - offset * 10
                code_draw.rounded_rectangle(
                    [30-offset, y_offset-offset, code_card.width-30+offset, y_offset+145+offset],
                    radius=18, fill=self.hex_to_rgb('#00ff88') + (alpha,)
                )
            
            code_draw.rounded_rectangle(
                [30, y_offset, code_card.width-30, y_offset+145],
                radius=18, fill=(0, 50, 25, 220)
            )
            
            # OUTPUT label
            code_draw.text((50, y_offset + 15), "▶ OUTPUT:", fill='#00ff88', font=output_font)
            
            # Typing output
            displayed_output = output_text[:output_progress]
            code_draw.text((50, y_offset + 65), displayed_output, fill='#ffffff', font=output_font)
            
            # Output cursor
            if output_progress < len(output_text):
                cursor_x = 50 + code_draw.textbbox((0, 0), displayed_output, font=output_font)[2]
                code_draw.rectangle([cursor_x, y_offset+65, cursor_x+3, y_offset+105], fill='#ffffff')
        
        code_x = (self.width - code_card.width) // 2
        frame.paste(code_card, (code_x, 320), code_card)
        
        # CTA card
        cta_card = self.create_glassmorphism_card(self.width - 60, 200, scheme)
        cta_draw = ImageDraw.Draw(cta_card)
        
        cta_text = "LIKE & FOLLOW"
        bbox = cta_draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_x = ((self.width - 60) - (bbox[2] - bbox[0])) // 2
        self.draw_text_with_glow(cta_draw, (cta_x, 45), cta_text, cta_font, '#ffffff', scheme['accent'])
        
        sub_text = f"Day {day + 1} Coming Soon!"
        bbox2 = cta_draw.textbbox((0, 0), sub_text, font=output_font)
        sub_x = ((self.width - 60) - (bbox2[2] - bbox2[0])) // 2
        cta_draw.text((sub_x, 125), sub_text, fill=self.hex_to_rgb(scheme['accent']), font=output_font)
        
        frame.paste(cta_card, (30, self.height - 270), cta_card)
        
        return np.array(frame)

    def create_video(self, day_data, audio_path, scheme):
        """Create video with typing animation"""
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        code = day_data['code']
        code_lines = code.split('\n')
        
        # Execute code to get real output
        output_text = self.execute_python_code(code)
        
        print(f"Code output: {output_text if output_text else 'None'}")
        
        # Animation timing
        total_frames = int(duration * self.fps)
        
        # Phase 1: Type code (60% of time)
        code_frames = int(total_frames * 0.6)
        # Phase 2: Show output (30% of time)
        output_frames = int(total_frames * 0.3) if output_text else 0
        # Phase 3: Hold (10% of time)
        
        frames = []
        
        # Calculate typing speed - SLOWER
        total_chars = sum(len(line) for line in code_lines)
        # Slow down: 1 character every 2 frames instead of multiple chars per frame
        chars_per_frame = 0.5 if code_frames > 0 else 1
        
        current_line = 0
        current_char = 0.0  # Changed to float for slower typing
        code_progress = []
        
        # Generate frames
        for frame_num in range(total_frames):
            # Code typing phase
            if frame_num < code_frames:
                if current_line < len(code_lines):
                    line = code_lines[current_line]
                    
                    if int(current_char) <= len(line):
                        if current_line >= len(code_progress):
                            code_progress.append('')
                        code_progress[current_line] = line[:int(current_char)]
                        current_char += chars_per_frame  # Slower increment
                    else:
                        current_line += 1
                        current_char = 0.0
                
                frame = self.create_video_frame(
                    scheme, day_data['day'], day_data['title'], 
                    code_lines, output_text, code_progress, 0, False
                )
            
            # Output typing phase
            elif output_text and frame_num < code_frames + output_frames:
                # Ensure code is complete
                code_progress = code_lines.copy()
                
                output_progress = int(((frame_num - code_frames) / output_frames) * len(output_text))
                
                frame = self.create_video_frame(
                    scheme, day_data['day'], day_data['title'], 
                    code_lines, output_text, code_progress, output_progress, True
                )
            
            # Hold phase
            else:
                code_progress = code_lines.copy()
                frame = self.create_video_frame(
                    scheme, day_data['day'], day_data['title'], 
                    code_lines, output_text, code_progress, 
                    len(output_text) if output_text else 0, bool(output_text)
                )
            
            frames.append(frame)
        
        # Create video
        def make_frame(t):
            frame_idx = int(t * self.fps)
            return frames[min(frame_idx, len(frames) - 1)]
        
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

#python #coding #programming #shorts #viral #codingtutorial #pythonforbeginners"""

        tags = ["python", "programming", "coding", "tutorial", "shorts"]
        
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
            
            # Cleanup
            for temp_file in self.output_folder.glob("temp_*"):
                try:
                    temp_file.unlink()
                except:
                    pass
            
            time.sleep(2)

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.create_all_videos("content.json", language="python")
    
    print("\n✨ ALL VIDEOS GENERATED!")
    print(f"📁 Videos in: {automation.output_folder}")
