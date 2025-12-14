import json
import os
import requests
import time
from pathlib import Path
from moviepy.editor import VideoClip, AudioFileClip, AudioClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
from datetime import datetime

# Google API imports
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeAutomation:
    def __init__(self):
        # Sanitize keys by stripping whitespace
        self.elevenlabs_keys = [
            os.getenv('ELEVENLABS_KEY_1', '').strip(),
            os.getenv('ELEVENLABS_KEY_2', '').strip(),
            os.getenv('ELEVENLABS_KEY_3', '').strip()
        ]
        # Filter out empty keys
        self.elevenlabs_keys = [k for k in self.elevenlabs_keys if k]
        
        self.current_key_index = 0
        
        # YouTube Credentials
        self.yt_client_id = os.getenv('YOUTUBE_CLIENT_ID', '').strip()
        self.yt_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET', '').strip()
        self.yt_refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN', '').strip()
        
        self.output_folder = Path("output")
        self.output_folder.mkdir(exist_ok=True)
        
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
        # Modern color schemes
        self.color_schemes = [
            {"name": "matrix", "bg1": "#001a0f", "bg2": "#003d20", "accent": "#00ff41", "text": "#ffffff", "badge": "#00ff41"},
            {"name": "cyber", "bg1": "#0a0e27", "bg2": "#1a1f4f", "accent": "#00d9ff", "text": "#ffffff", "badge": "#7b2ff7"},
            {"name": "neon", "bg1": "#1a0033", "bg2": "#330066", "accent": "#ff00ff", "text": "#ffffff", "badge": "#ff0080"},
            {"name": "sunset", "bg1": "#1a0a00", "bg2": "#4d1f00", "accent": "#ff6600", "text": "#ffffff", "badge": "#ff3300"},
            {"name": "ice", "bg1": "#001a33", "bg2": "#003366", "accent": "#00ffff", "text": "#ffffff", "badge": "#0099ff"},
        ]
        
        self.language_names = {
            "python": "Python",
            "javascript": "JavaScript",
            "java": "Java",
            "cpp": "C++",
            "go": "Go",
            "rust": "Rust",
            "php": "PHP",
            "ruby": "Ruby",
            "swift": "Swift",
            "kotlin": "Kotlin"
        }

    def load_content(self, json_path="content.json"):
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data

    def save_content(self, data, json_path="content.json"):
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_next_pending_day(self, data):
        for day in data['days']:
            if day.get('status') != 'uploaded':
                return day
        return None

    def generate_script(self, day_data):
        title = day_data['title']
        language = day_data.get('language', 'python')
        language_name = self.language_names.get(language, language.capitalize())
        explanation = day_data.get('explanation', '')
        day = day_data['day']
        
        scripts = [
            f"Hey coders! Welcome to Day {day}. Today we're learning {title} in {language_name}. "
            f"This is super important, so pay attention! "
            f"Here's the code. Let me break it down for you. "
            f"{explanation} "
            f"Pretty cool, right? Practice this and you'll master it! "
            f"Like and follow for Day {day + 1}!",
            
            f"What's up everyone! Day {day} is here! "
            f"Today's topic: {title} in {language_name}. This is going to be awesome! "
            f"Check out this code. "
            f"{explanation} "
            f"See how simple that is? Now you try it! "
            f"Drop a like if you learned something new!",
        ]
        return random.choice(scripts)

    def text_to_speech_elevenlabs(self, text, output_path):
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        if not self.elevenlabs_keys:
            print("❌ No ElevenLabs API keys found in environment variables!")
            return False

        for attempt in range(len(self.elevenlabs_keys)):
            api_key = self.elevenlabs_keys[self.current_key_index]
            
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "INVALID"
            print(f"🔄 Attempting TTS with key {masked_key} (Index: {self.current_key_index})")
            
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
                    "similarity_boost": 0.75,
                }
            }
            
            try:
                response = requests.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Audio generated successfully")
                    return True
                elif response.status_code == 401:
                    print(f"⚠️ Auth failed (401) for key {masked_key}. Response: {response.text}")
                    self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
                else:
                    print(f"❌ API Error: {response.status_code} - {response.text}")
                    self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
            except Exception as e:
                print(f"❌ Exception generating audio: {e}")
                self.current_key_index = (self.current_key_index + 1) % len(self.elevenlabs_keys)
        
        print("❌ All ElevenLabs keys failed.")
        return False

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_syntax_color(self, line, language):
        language = language.lower()
        if language == "python":
            if any(kw in line for kw in ['print', 'def', 'class', 'if', 'else', 'for', 'while', 'import', 'return', 'True', 'False']):
                return '#ff3e9d'
            elif '"' in line or "'" in line:
                return '#00ff88'
            elif any(c.isdigit() for c in line):
                return '#ffff00'
        return '#ffffff'

    def create_gradient_bg(self, width, height, color1, color2):
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
        card = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        glass = Image.new('RGBA', (width, height), (255, 255, 255, 25))
        card = Image.alpha_composite(card, glass)
        draw = ImageDraw.Draw(card)
        accent_rgb = self.hex_to_rgb(scheme['accent'])
        for i in range(8, 0, -2):
            alpha = int(100 - i * 10)
            draw.rounded_rectangle([i, i, width-i, height-i], radius=25, 
                                   outline=accent_rgb + (alpha,), width=3)
        card = card.filter(ImageFilter.GaussianBlur(3))
        return card

    def draw_text_with_glow(self, draw, pos, text, font, color, glow_color=None):
        if glow_color is None:
            glow_color = color
        glow_rgb = self.hex_to_rgb(glow_color) if isinstance(glow_color, str) else glow_color
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2), (3,3), (-3,-3)]:
            draw.text((pos[0]+offset[0], pos[1]+offset[1]), text, 
                     fill=glow_rgb + (60,), font=font)
        draw.text(pos, text, fill=color, font=font)

    def create_video_frame(self, scheme, day, title, language, code_lines, output_text, 
                          code_progress, output_progress, show_output):
        frame = self.create_gradient_bg(self.width, self.height, scheme['bg1'], scheme['bg2'])
        draw = ImageDraw.Draw(frame)
        grid_color = self.hex_to_rgb(scheme['accent'])
        for x in range(0, self.width, 100):
            for y in range(0, self.height, 100):
                draw.rectangle([x, y, x+1, y+1], fill=grid_color + (20,))
        
        title_card = self.create_glassmorphism_card(self.width - 80, 180, scheme)
        
        try:
            if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
                code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)
                day_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
                output_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 36)
                cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
            else:
                title_font = ImageFont.load_default()
                code_font = ImageFont.load_default()
                day_font = ImageFont.load_default()
                output_font = ImageFont.load_default()
                cta_font = ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            code_font = ImageFont.load_default()
            day_font = ImageFont.load_default()
            output_font = ImageFont.load_default()
            cta_font = ImageFont.load_default()
        
        title_draw = ImageDraw.Draw(title_card)
        full_title = f"Day {day}: {title}"
        
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
        
        num_lines = len(code_lines)
        card_height = 250 + num_lines * 60
        if show_output and output_text:
            card_height += 180
        
        code_card = self.create_glassmorphism_card(int(self.width * 0.92), card_height, scheme)
        code_draw = ImageDraw.Draw(code_card)
        
        badge_w, badge_h = 220, 95
        badge_x, badge_y = 35, 30
        badge_rgb = self.hex_to_rgb(scheme['badge'])
        
        pulse_value = len(code_progress) if code_progress else 0
        pulse = abs(np.sin(pulse_value * 0.2) * 0.3) + 0.7
        for offset in range(15, 0, -2):
            alpha = int(150 * pulse - offset * 10)
            code_draw.rounded_rectangle(
                [badge_x-offset, badge_y-offset, badge_x+badge_w+offset, badge_y+badge_h+offset],
                radius=25, fill=badge_rgb + (max(0, alpha),)
            )
        
        code_draw.rounded_rectangle([badge_x, badge_y, badge_x+badge_w, badge_y+badge_h], 
                                    radius=25, fill=badge_rgb)
        
        border_offset = int(3 * pulse)
        code_draw.rounded_rectangle(
            [badge_x+border_offset, badge_y+border_offset, 
             badge_x+badge_w-border_offset, badge_y+badge_h-border_offset],
            radius=25, outline=(255, 255, 255, 200), width=3
        )
        
        day_text = f"DAY {day}"
        bbox = code_draw.textbbox((0, 0), day_text, font=day_font)
        text_w = bbox[2] - bbox[0]
        text_x = badge_x + (badge_w - text_w) // 2
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
            code_draw.text((text_x+offset[0], badge_y+18+offset[1]), day_text, fill=(255, 255, 255, 100), font=day_font)
        code_draw.text((text_x, badge_y + 18), day_text, fill='#ffffff', font=day_font)
        
        y_offset = 150
        for i, line in enumerate(code_lines):
            if i < len(code_progress):
                displayed_line = code_progress[i]
            else:
                break
            if not displayed_line.strip():
                y_offset += 60
                continue
            color = self.get_syntax_color(displayed_line, language)
            self.draw_text_with_glow(code_draw, (55, y_offset), displayed_line, code_font, color, color)
            y_offset += 60
        
        if code_progress and len(code_progress[-1]) < len(code_lines[len(code_progress)-1]):
            cursor_y = 150 + (len(code_progress) - 1) * 60
            cursor_x = 55 + code_draw.textbbox((0, 0), code_progress[-1], font=code_font)[2]
            code_draw.rectangle([cursor_x, cursor_y, cursor_x+3, cursor_y+45], fill='#ffffff')
        
        if show_output and output_text:
            y_offset += 35
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
            code_draw.text((50, y_offset + 15), "▶ OUTPUT:", fill='#00ff88', font=output_font)
            displayed_output = output_text[:output_progress]
            code_draw.text((50, y_offset + 65), displayed_output, fill='#ffffff', font=output_font)
            if output_progress < len(output_text):
                cursor_x = 50 + code_draw.textbbox((0, 0), displayed_output, font=output_font)[2]
                code_draw.rectangle([cursor_x, y_offset+65, cursor_x+3, y_offset+105], fill='#ffffff')
        
        code_x = (self.width - code_card.width) // 2
        frame.paste(code_card, (code_x, 320), code_card)
        
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
        try:
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration
            print(f"   Audio duration: {duration:.2f}s")
        except Exception as e:
            print(f"⚠️ Audio file issue: {e}. Creating silent clip")
            duration = 10
            audio = AudioClip(lambda t: [0, 0], duration=duration, fps=44100)
        
        code = day_data['code']
        language = day_data.get('language', 'python')
        code_lines = code.split('\n')
        output_text = day_data.get('output', None)
        
        print(f"Language: {language}")
        print(f"Output: {output_text if output_text else 'None'}")
        
        total_frames = int(duration * self.fps)
        code_frames = int(total_frames * 0.6)
        output_frames = int(total_frames * 0.3) if output_text else 0
        
        frames = []
        chars_per_frame = 0.5 if code_frames > 0 else 1
        current_line = 0
        current_char = 0.0
        code_progress = []
        
        for frame_num in range(total_frames):
            if frame_num < code_frames:
                if current_line < len(code_lines):
                    line = code_lines[current_line]
                    if int(current_char) <= len(line):
                        if current_line >= len(code_progress):
                            code_progress.append('')
                        code_progress[current_line] = line[:int(current_char)]
                        current_char += chars_per_frame
                    else:
                        current_line += 1
                        current_char = 0.0
                frame = self.create_video_frame(scheme, day_data['day'], day_data['title'], language,
                    code_lines, output_text, code_progress, 0, False)
            elif output_text and frame_num < code_frames + output_frames:
                code_progress = code_lines.copy()
                output_progress = int(((frame_num - code_frames) / output_frames) * len(output_text))
                frame = self.create_video_frame(scheme, day_data['day'], day_data['title'], language,
                    code_lines, output_text, code_progress, output_progress, True)
            else:
                code_progress = code_lines.copy()
                frame = self.create_video_frame(scheme, day_data['day'], day_data['title'], language,
                    code_lines, output_text, code_progress, len(output_text) if output_text else 0, bool(output_text))
            frames.append(frame)
        
        def make_frame(t):
            frame_idx = int(t * self.fps)
            return frames[min(frame_idx, len(frames) - 1)]
        
        video_clip = VideoClip(make_frame, duration=duration)
        video_clip = video_clip.set_audio(audio)
        return video_clip

    def generate_youtube_metadata(self, day_data):
        language = day_data.get('language', 'python')
        language_name = self.language_names.get(language, language.capitalize())
        title = f"Day {day_data['day']}: Learn {day_data['title']} in {language_name} 🚀 #shorts"
        description = f"""🔥 Day {day_data['day']} of the 30-Day Coding Challenge! 

Today we are learning about {day_data['title']} in {language_name}.
👇 CODE SNIPPET BELOW 👇

{day_data['code']}

💡 Explanation:
{day_data.get('explanation', 'Learning to code one step at a time!')}

👉 Subscribe for Day {day_data['day'] + 1}! Created with AI.
#coding #programming #{language} #learncoding #python #javascript #developer #tech #tutorial"""
        tags = [language, f"{language} tutorial", "coding for beginners", "programming", "learn to code",
                "developer", "tech", "daily coding", "software engineer", "shorts"]
        return {"title": title[:100], "description": description, "tags": tags, "category": "27", "privacyStatus": "public"}

    def upload_to_youtube(self, video_path, metadata):
        if not self.yt_refresh_token or not self.yt_client_id:
            print("⚠️ YouTube credentials missing. Skipping upload.")
            return False
        try:
            print("🚀 Authenticating with YouTube...")
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(
                info={"client_id": self.yt_client_id, "client_secret": self.yt_client_secret, "refresh_token": self.yt_refresh_token}
            )
            youtube = build("youtube", "v3", credentials=credentials)
            body = {
                "snippet": {"title": metadata["title"], "description": metadata["description"], "tags": metadata["tags"], "categoryId": metadata["category"]},
                "status": {"privacyStatus": metadata["privacyStatus"], "selfDeclaredMadeForKids": False}
            }
            print(f"📤 Uploading: {video_path}")
            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   Upload progress: {int(status.progress() * 100)}%")
            print(f"✅ Upload Complete! Video ID: {response['id']}")
            return True
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
            return False

    def run_daily_automation(self, json_path="content.json"):
        print(f"📂 Loading content from {json_path}")
        data = self.load_content(json_path)
        day_data = self.get_next_pending_day(data)
        if not day_data:
            print("🎉 No pending videos! All days have been uploaded.")
            return
        
        print(f"\n{'='*50}")
        print(f"🔥 Processing Day {day_data['day']}: {day_data['title']}")
        print(f"{'='*50}")
        
        scheme = random.choice(self.color_schemes)
        script = self.generate_script(day_data)
        audio_path = self.output_folder / f"day_{day_data['day']}_audio.mp3"
        print("🎙️ Generating Audio...")
        
        if not self.text_to_speech_elevenlabs(script, str(audio_path)):
            print("⚠️ Audio generation failed or no keys available. Creating silent fallback.")
            from moviepy.audio.AudioClip import AudioArrayClip
            import numpy as np
            duration = 10
            silence = np.zeros((int(duration * 44100), 2))
            silent_clip = AudioArrayClip(silence, fps=44100)
            silent_clip.write_audiofile(str(audio_path), fps=44100)
        
        print("🎥 Generating Video...")
        time.sleep(1)
        video = self.create_video(day_data, audio_path, scheme)
        video_path = self.output_folder / f"day_{day_data['day']}_shorts.mp4"
        video.write_videofile(str(video_path), fps=self.fps, codec='libx264', audio_codec='aac', preset='medium', bitrate='5000k', audio_fps=44100)
        
        metadata = self.generate_youtube_metadata(day_data)
        with open(self.output_folder / f"day_{day_data['day']}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        upload_success = self.upload_to_youtube(video_path, metadata)
        if upload_success:
            print("📝 Updating content.json status...")
            day_data['status'] = 'uploaded'
            day_data['upload_date'] = datetime.now().strftime("%Y-%m-%d")
            self.save_content(data, json_path)
            print("✅ Status updated to 'uploaded'")
        else:
            print("⚠️ Video generated but NOT uploaded (check credentials). Status not updated.")

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.run_daily_automation("content.json")
