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

import math

import math

try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

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

        # Google AI Key
        self.google_ai_key = os.getenv('GOOGLE_AI_API_KEY', '').strip() or os.getenv('GEMINI_API_KEY', '').strip()
        
        # Initialize Gemini if key exists
        if self.google_ai_key:
            print(f"🔑 Gemini API Key found (Length: {len(self.google_ai_key)})")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_ai_key)
                
                # Dynamic Model Discovery
                print("🔍 Discovering available AI models...", flush=True)
                active_model = None
                
                # Priority list of models to check for
                PREFERRED_MODELS = [
                    "models/gemini-2.5-flash",
                    "models/gemini-2.5-pro",
                    "models/gemini-2.0-flash",
                    "models/gemini-1.5-flash",
                    "models/gemini-1.5-pro",
                    "models/gemini-pro"
                ]
                
                try:
                    found_models = []
                    # List models but stop if we find a high-priority one, or limit 
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            print(f"   - Found: {m.name}", flush=True)
                            found_models.append(m.name)
                            
                            # If we found our top preference, stop searching (optimization)
                            if m.name == PREFERRED_MODELS[0]:
                                active_model = m.name
                                break
                    
                    # Select the best available model from our preferences
                    if not active_model:
                        for pref in PREFERRED_MODELS:
                            if pref in found_models:
                                active_model = pref
                                break
                    
                    # Fallback to the first 'gemini' model found if none of the preferences match
                    if not active_model:
                        for m_name in found_models:
                            if 'gemini' in m_name.lower():
                                active_model = m_name
                                break

                    if active_model:
                        print(f"✅ Selected Model: {active_model}", flush=True)
                        self.genai_model = genai.GenerativeModel(active_model)
                    else:
                        print("⚠️ No specific 'gemini' model found, defaulting to 'gemini-pro'", flush=True)
                        self.genai_model = genai.GenerativeModel('gemini-pro')
                        
                    self.has_ai = True
                except Exception as list_err:
                     print(f"⚠️ Failed to list models (Auth/Region issue?): {list_err}", flush=True)
                     # Try fallback anyway
                     self.genai_model = genai.GenerativeModel('gemini-pro')
                     self.has_ai = True
            except Exception as e:
                print(f"⚠️ AI Initialization Failed: {e}")
                self.has_ai = False
        else:
            print("❌ Gemini API Key NOT found in environment variables.")
            self.has_ai = False
        
        self.output_folder = Path("output")
        self.output_folder.mkdir(exist_ok=True)
        
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
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
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Decode Error in {json_path}: {e}")
            print("🔄 Attempting to repair JSON...")
            return self.repair_json(json_path)

    def repair_json(self, json_path):
        """Attempts to fix common JSON corruptions like 'Extra data'."""
        with open(json_path, 'r') as f:
            content = f.read()
        
        # Scenario 1: Extra Data (e.g. Concatenated JSONs) - take the first valid object
        try:
            from json import JSONDecoder
            decoder = JSONDecoder()
            data, index = decoder.raw_decode(content)
            print(f"   ✅ Recovered valid JSON (First {index} bytes used).")
            # Optional: Save back the clean version immediately
            self.save_content(data, json_path) 
            return data
        except Exception as repair_error:
            print(f"   ❌ Repair failed: {repair_error}")
            raise repair_error  # Re-raise the repair error

    def save_content(self, data, json_path="content.json"):
        import tempfile
        import shutil
        
        # Atomic Write: Write to temp file first, then move to destination
        # This prevents file corruption if the script crashes during write
        temp_file = None
        try:
            # Create temp file in the same directory to ensure atomic move works
            dir_name = os.path.dirname(json_path) or '.'
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=dir_name) as tmp:
                json.dump(data, tmp, indent=2)
                temp_file = tmp.name
            
            # Atomic move
            shutil.move(temp_file, json_path)
        except Exception as e:
            print(f"❌ Failed to save content: {e}")
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def get_next_pending_day(self, data):
        for day in data['days']:
            if day.get('status') != 'uploaded':
                return day
        return None

    def generate_dynamic_theme(self, topic):
        """Generates a unique color scheme for the video using AI or Random Logic."""
        if self.has_ai:
            try:
                prompt = f"""
                Generate a dark, modern, high-contrast color palette for a video about "{topic}".
                Return ONLY a JSON object with keys: "bg1", "bg2" (gradients), "accent" (bright), "text", "badge".
                Use hex codes. Example: purity, cyber, matrix styles.
                """
                response = self.genai_model.generate_content(prompt)
                text = response.text.replace('```json', '').replace('```', '').strip()
                scheme = json.loads(text)
                scheme['name'] = 'ai_generated'
                return scheme
            except Exception as e:
                print(f"⚠️ AI Theme Gen Failed: {e}. Using Random.")
        
        # Fallback Random Logic
        hues = [0, 30, 60, 120, 180, 240, 280, 330] # Random base hues
        base_hue = random.choice(hues)
        
        def hsv_to_hex(h, s, v):
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
            return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
            
        return {
            "name": "dynamic_random",
            "bg1": hsv_to_hex(base_hue, 0.9, 0.1), # Very dark background
            "bg2": hsv_to_hex(base_hue, 0.8, 0.2), # Slightly lighter gradient
            "accent": hsv_to_hex((base_hue + 180) % 360, 1.0, 1.0), # Complementary accent
            "text": "#ffffff",
            "badge": hsv_to_hex((base_hue + 180) % 360, 0.8, 0.8)
        }




    def generate_script(self, day_data):
        """Generates a viral spoken script based on the provided explanation."""
        title = day_data['title']
        explanation = day_data.get('explanation', '')
        language = day_data.get('language', 'python')
        day = day_data['day']
        hook = day_data.get('hook', '')
        cta = day_data.get('cta', '')

        if self.has_ai:
            try:
                # Determine broader topic from data or default to General
                category = day_data.get('category', 'Education')
                
                prompt = f"""
                Write a 30-45 second spoken script for a YouTube Short.
                
                CONTEXT:
                - Series: Day {day} of 30 Days of Learning.
                - Topic: {title} ({language})
                - The content/code and explanation are provided below.
                
                SOURCE MATERIAL:
                "{explanation}"
                
                MANDATORY STRUCTURE:
                1. HOOK: "{hook}" (Read this EXACTLY as written, with high energy)
                2. BODY: Explain the concept simply using the source material.
                3. OUTRO: "{cta}" (Read this EXACTLY)
                
                REQUIREMENTS:
                1. Tone: Energetic, Fast-paced, Viral. 
                2. Return ONLY the spoken text. No "Scene 1" labels.
                3. USE DRAMATIC PUNCTUATION:
                   - Use CAPS for emphasis (e.g. "STOP scrolling!")
                   - Use "..." for suspense.
                   - Use "!" for excitement.
                """
                response = self.genai_model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"⚠️ AI Script Gen Failed: {e}. Using Template.")

        # Fallback Template using new viral fields
        language_name = self.language_names.get(language, language.capitalize())
        
        script = f"{hook} Welcome to Day {day} of learning {language_name}! " \
                 f"Today is all about {title}. Look at this code... {explanation} " \
                 f"{cta} See you tomorrow!"
        return script.replace("Sub ", "Subscribe ")

    def check_elevenlabs_quota(self, api_key, index):
        """Check user subscription and quota status"""
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": api_key}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                char_count = data.get('character_count', 0)
                char_limit = data.get('character_limit', 0)
                remaining = char_limit - char_count
                print(f"   🔑 Key {index}: {remaining}/{char_limit} chars remaining (Tier: {data.get('tier', 'unknown')})")
                return remaining
            else:
                masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                print(f"   ❌ Key {index} ({masked_key}) Check Failed: {response.status_code}")
                return 0
        except Exception as e:
            print(f"   ❌ Key {index} Exception: {e}")
            return 0

    def text_to_speech_elevenlabs(self, text, output_path):
        """
        Generates speech using ElevenLabs API with smart key rotation.
        Falls back to Google TTS (gTTS - free) if all ElevenLabs keys are exhausted.
        """
        # Josh Voice - Clear, confident male voice, great for tutorials
        VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"  # Josh
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        
        # --- ElevenLabs Attempt ---
        if self.elevenlabs_keys:
            print("\n🔍 Checking ElevenLabs API Keys Quota...")
            valid_key = None
            
            for i, key in enumerate(self.elevenlabs_keys):
                remaining = self.check_elevenlabs_quota(key, i)
                # Need about 50 extra chars for safety margin
                if remaining > len(text) + 50:
                    print(f"   ✅ Key {i} selected (Has {remaining} chars, need ~{len(text)})")
                    valid_key = key
                    self.current_key_index = i
                    break
                else:
                    print(f"   ⚠️ Key {i} skipped (Insufficient quota or invalid)")
            
            if valid_key:
                print(f"🔄 Generating Audio with ElevenLabs Key {self.current_key_index}...")
                
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": valid_key
                }
                
                # Balanced voice settings for clarity + emotion
                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.40,           # Balanced: 0.3-0.5 is stable but expressive
                        "similarity_boost": 0.75,
                        "style": 0.50,               # Moderate exaggeration
                        "use_speaker_boost": True
                    }
                }
                
                try:
                    response = requests.post(url, json=data, headers=headers)
                    
                    if response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        print(f"✓ ElevenLabs Audio generated successfully")
                        return True
                    elif response.status_code == 401:
                        print(f"⚠️ Auth failed (401). Response: {response.text}")
                    else:
                        print(f"❌ ElevenLabs API Error: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"❌ ElevenLabs Exception: {e}")
            else:
                print("⚠️ All ElevenLabs keys exhausted. Trying free fallback...")
        else:
            print("⚠️ No ElevenLabs API keys configured. Using free fallback...")
        
        # --- Free Fallback: Google TTS (gTTS) ---
        print("🔄 Generating Audio with Google TTS (Free Fallback)...")
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            print(f"✓ gTTS Audio generated successfully (Free)")
            return True
        except ImportError:
            print("❌ gTTS not installed. Install with: pip install gTTS")
        except Exception as e:
            print(f"❌ gTTS Exception: {e}")
        
        return False

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_text_chunks(self, text, language):
        """
        Returns a list of (text_segment, hex_color) tuples for syntax highlighting.
        Uses Pygments if available, otherwise falls back to simple logic.
        """
        if not text:
            return []
            
        chunks = []
        
        if HAS_PYGMENTS:
            try:
                # Map Pygments Token types to Hex Colors
                # Dracular/Monokai-ish style
                STYLE_MAP = {
                    Token.Keyword: '#ff79c6',       # Pink
                    Token.Keyword.Declaration: '#8be9fd', # Cyan (def, class)
                    Token.Keyword.Namespace: '#ff79c6',   # Pink (import)
                    Token.Name.Function: '#50fa7b', # Green
                    Token.Name.Class: '#50fa7b',    # Green
                    Token.Name.Builtin: '#8be9fd',  # Cyan
                    Token.String: '#f1fa8c',        # Yellow
                    Token.Number: '#bd93f9',        # Purple
                    Token.Operator: '#ff79c6',      # Pink
                    Token.Comment: '#6272a4',       # Grey/Blue
                    Token.Text: '#f8f8f2',          # White
                    Token.Literal: '#bd93f9',
                    Token.Punctuation: '#f8f8f2'
                }
                
                try:
                    lexer = get_lexer_by_name(language)
                except:
                    lexer = get_lexer_by_name("text")
                    
                tokens = lex(text, lexer)
                
                for token_type, value in tokens:
                    # Find best color match (walk up the token hierarchy)
                    color = '#f8f8f2' # Default white
                    parent = token_type
                    while parent:
                        if parent in STYLE_MAP:
                            color = STYLE_MAP[parent]
                            break
                        parent = parent.parent
                    
                    chunks.append((value, color))
                return chunks
                
            except Exception as e:
                print(f"Pygments Error: {e}")
                # Fallthrough to fallback
        
        # --- FALLBACK (Old logic) ---
        # Generic Syntax Highlighting for ANY language
        keywords = [
            'print', 'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'import', 'return', 
            'true', 'false', 'null', 'none', 'var', 'let', 'const', 'function', 'func', 
            'public', 'private', 'protected', 'void', 'int', 'string', 'bool', 'float'
        ]
        
        line_lower = text.lower()
        color = '#ffffff'
        
        if text.strip().startswith('#') or text.strip().startswith('//'):
            color = '#808080'
        elif any(f"{kw}" in line_lower for kw in keywords):
            color = '#ff3e9d'
        elif '"' in text or "'" in text:
            color = '#00ff88'
        elif any(c.isdigit() for c in text):
            color = '#ffff00'
            
        return [(text, color)]

    def get_color_shift(self, hex_color, t, speed=0.5):
        """Shifts the hue of a color over time."""
        import colorsys
        r, g, b = self.hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        new_h = (h + t * speed) % 1.0
        r, g, b = colorsys.hsv_to_rgb(new_h, s, v)
        return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

    def create_animated_bg(self, width, height, color1, color2, t):
        """Creates a gradient using numpy for speed."""
        c1 = self.get_color_shift(color1, t, 0.1)
        c2 = self.get_color_shift(color2, t, 0.15)
        
        # Use simple gradient calculation with numpy if possible, or fallback to efficient line drawing
        # For 30FPS rendering, we need speed. 
        # Let's use a simpler approach: Pre-calculate the gradient line and tile it?
        # No, let's just use the existing logic but with shifted colors and optimized drawing.
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Color shifting already makes it dynamic. 
        # To make it faster, we can draw fewer lines (interpolated) or use a smaller image and resize.
        # Resizing from a smaller gradient is much faster and looks smooth for gradients.
        
        small_h = 100 # Generate gradient at low res
        r1, g1, b1 = self.hex_to_rgb(c1)
        r2, g2, b2 = self.hex_to_rgb(c2)
        
        # Create array of colors
        channels = []
        for c_start, c_end in [(r1, r2), (g1, g2), (b1, b2)]:
            arr = np.linspace(c_start, c_end, small_h)
            channels.append(arr)
            
        # Stack and resize
        gradient = np.dstack(channels).astype(np.uint8) # Shape (small_h, 1, 3)
        # Repeat to fill width (only need 1 pixel width actually)
        gradient = np.tile(gradient, (1, 1, 1)) # Keep it 1px wide for resize
        
        grad_img = Image.fromarray(gradient)
        grad_img = grad_img.resize((width, height), resample=Image.Resampling.LANCZOS)
        
        return grad_img

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
                          code_progress, output_progress, show_output, t_val=0, total_duration=10):
        
        frame = self.create_animated_bg(self.width, self.height, scheme['bg1'], scheme['bg2'], t_val)
        draw = ImageDraw.Draw(frame)
        
        # Moving Grid
        grid_color = self.hex_to_rgb(scheme['accent'])
        grid_offset_y = int(t_val * 20) % 100
        grid_offset_x = int(t_val * 10) % 100
        
        for x in range(0 - grid_offset_x, self.width, 100):
            for y in range(0 - grid_offset_y, self.height, 100):
                 # Use transparency for subtle grid
                draw.rectangle([x, y, x+1, y+1], fill=grid_color + (30,))
        
        
        
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

        # --- TITLE LOGIC (Dynamic Height & Emoji Stripping) ---
        import re
        # Strip emojis for video display (keep ASCII + basic punctuation)
        clean_title = title.encode('ascii', 'ignore').decode('ascii').strip()
        full_title = f"Day {day}: {clean_title}"
        
        # Word Wrap
        title_draw_temp = ImageDraw.Draw(Image.new('RGBA', (1,1))) # Temp for measuring
        words = full_title.split()
        lines = []
        current_line = []
        
        max_width = self.width - 180
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = title_draw_temp.textbbox((0, 0), test_line, font=title_font)
            if (bbox[2] - bbox[0]) < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
            
        # Calculate Dynamic Height
        line_height = 70
        padding = 50
        card_h = (len(lines) * line_height) + (padding * 2)
        
        # Create Card
        title_card = self.create_glassmorphism_card(self.width - 80, card_h, scheme)
        title_draw = ImageDraw.Draw(title_card)
        
        y = padding
        for line in lines:
            bbox = title_draw.textbbox((0, 0), line, font=title_font)
            x = ((self.width - 80) - (bbox[2] - bbox[0])) // 2
            self.draw_text_with_glow(title_draw, (x, y), line, title_font, '#ffffff', scheme['accent'])
            y += line_height
            
        frame.paste(title_card, (40, 50), title_card)
        
        # --- SCROLLING LOGIC ---
        MAX_LINES = 14
        active_line_idx = len(code_progress) - 1
        # Calculate scroll offset to keep active line within view
        # We start scrolling when we go past MAX_LINES - 3
        scroll_offset = max(0, active_line_idx - (MAX_LINES - 3)) 
        
        visible_lines = code_lines[scroll_offset : scroll_offset + MAX_LINES]
        
        # Fixed height for code card to ensure fit, large enough for code + output
        card_height = 1200 
        
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
        
        # Draw Code Lines (Scrolled)
        for i, line in enumerate(visible_lines):
            # The line index in the original list is (i + scroll_offset)
            original_idx = i + scroll_offset
            
            if original_idx < len(code_progress):
                displayed_line = code_progress[original_idx]
            else:
                break # Don't draw future lines
                
            line_num_str = f"{original_idx + 1}."
            
            # --- DEBUG MODE: HIGHLIGHT ACTIVE LINE ---
            # If this is the active line being typed (last line in progress), highlight it
            if original_idx == len(code_progress) - 1 and len(code_progress) <= len(code_lines):
                 # Draw semi-transparent rectangle behind the line
                 highlight_color = self.hex_to_rgb(scheme['accent'])
                 # Calculate width based on code card width (approx)
                 highlight_w = code_card.width - 20
                 # Draw with low alpha for subtle highlight
                 code_draw.rectangle([10, y_offset, 10 + highlight_w, y_offset + 50], fill=highlight_color + (50,))

            self.draw_text_with_glow(code_draw, (15, y_offset), line_num_str, code_font, '#888888', '#888888')
            
            if not displayed_line.strip():
                y_offset += 60
                continue
            
            # Syntax Highlighting with Chunks
            chunks = self.get_text_chunks(displayed_line, language)
            
            x_current = 85
            for chunk_text, chunk_color in chunks:
                self.draw_text_with_glow(code_draw, (x_current, y_offset), chunk_text, code_font, chunk_color, chunk_color)
                # Calculate width of this chunk to advance cursor
                try:
                    chunk_w = code_draw.textbbox((0,0), chunk_text, font=code_font)[2]
                except: chunk_w = 0
                x_current += chunk_w
                
            y_offset += 60
        
        # Cursor logic
        if code_progress:
            last_visible_idx = len(code_progress) - 1 - scroll_offset
            # Only draw cursor if it's within visible range
            if 0 <= last_visible_idx < MAX_LINES:
                current_line_content = code_progress[-1]
                cursor_y = 150 + last_visible_idx * 60
                
                try:
                    width_of_text = code_draw.textbbox((0, 0), current_line_content, font=code_font)[2]
                except: width_of_text = 0
                cursor_x = 85 + width_of_text
                
                # Blinking effect
                if int(t_val * 2) % 2 == 0:
                    code_draw.rectangle([cursor_x, cursor_y, cursor_x+5, cursor_y+45], fill='#ffffff')

        # Output logic (Pinned to bottom of card)
        if show_output and output_text:
            # Wrap output text to calculate dynamic height
            out_lines = []
            curr_l = ""
            displayed_output = output_text[:output_progress]
            
            # Pre-calculate ALL lines to determine full height needed
            full_out_lines = []
            temp_l = ""
            for char in output_text: # Calculate based on FULL text to size box correctly from start
                if char == '\n':
                    full_out_lines.append(temp_l)
                    temp_l = ""
                else:
                    temp_l += char
                    # Approx char limit per line
                    if len(temp_l) > 30: 
                         full_out_lines.append(temp_l)
                         temp_l = ""
            if temp_l: full_out_lines.append(temp_l)
            
            # Dynamic Height Calculation
            # Base height 145 (approx 3 lines) -> each extra line adds ~40px
            # Cap at some reasonable max to avoid covering too much code (e.g., 6 lines)
            num_lines = len(full_out_lines)
            
            # Min 3 lines, Max 8 lines
            display_lines_count = max(3, min(8, num_lines))
            
            line_height = 40
            padding_top = 15
            padding_bottom = 25 # Space for cursor/padding
            header_height = 40
            
            output_box_height = header_height + (display_lines_count * line_height) + padding_bottom
            
            output_y_start = card_height - output_box_height - 30 # 30px margin from bottom
            
            # Draw output container
            for offset in range(8, 0, -2):
                alpha = 80 - offset * 10
                code_draw.rounded_rectangle(
                    [30-offset, output_y_start-offset, code_card.width-30+offset, output_y_start+output_box_height+offset],
                    radius=18, fill=self.hex_to_rgb('#00ff88') + (alpha,)
                )
            code_draw.rounded_rectangle(
                [30, output_y_start, code_card.width-30, output_y_start+output_box_height],
                radius=18, fill=(0, 50, 25, 220)
            )
            code_draw.text((50, output_y_start + 15), "▶ OUTPUT:", fill='#00ff88', font=output_font)
            
            # Re-process displayed lines for actual rendering
            out_lines = []
            curr_l = ""
            for char in displayed_output:
                if char == '\n':
                    out_lines.append(curr_l)
                    curr_l = ""
                else:
                    curr_l += char
                    if len(curr_l) > 30: 
                         out_lines.append(curr_l)
                         curr_l = ""
            if curr_l: out_lines.append(curr_l)
            
            # Show last N visible lines based on dynamic height
            visible_out = out_lines[-display_lines_count:]
            
            out_y = output_y_start + 65
            for ol in visible_out:
                code_draw.text((50, out_y), ol, fill='#ffffff', font=output_font)
                out_y += 40
                
            # Cursor for output
            # Cursor for output (Follows text)
            if output_progress < len(output_text):
                 if int(t_val * 4) % 2 == 0:
                    # Calculate width of last visible line to position cursor
                    last_line_width = 0
                    if visible_out:
                        try:
                            last_line_width = code_draw.textbbox((0, 0), visible_out[-1], font=output_font)[2]
                        except: pass
                    
                    cursor_x_out = 50 + last_line_width + 2
                    cursor_y_out = out_y - 40 # out_y was incremented after loop, move back to last line
                    
                    code_draw.rectangle([cursor_x_out, cursor_y_out, cursor_x_out+10, cursor_y_out+35], fill='#ffffff')

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
        
        # Progress Bar at the top
        progress_pct = min(1.0, t_val / total_duration)
        bar_height = 15
        draw.rectangle([0, 0, int(self.width * progress_pct), bar_height], fill=self.hex_to_rgb(scheme['accent']))
        
        frame.paste(cta_card, (30, self.height - 270), cta_card)
        return np.array(frame)

    def create_video(self, day_data, audio_path, scheme):
        try:
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration + 1.5 # Add 1.5s buffer for pacing
            print(f"   Audio duration: {audio.duration:.2f}s (+1.5s buffer = {duration:.2f}s)")
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
            
            t_val = frame_num / self.fps

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
                    code_lines, output_text, code_progress, 0, False, t_val=t_val, total_duration=duration)
            elif output_text and frame_num < code_frames + output_frames:
                code_progress = code_lines.copy()
                output_progress = int(((frame_num - code_frames) / output_frames) * len(output_text))
                frame = self.create_video_frame(scheme, day_data['day'], day_data['title'], language,
                    code_lines, output_text, code_progress, output_progress, True, t_val=t_val, total_duration=duration)
            else:
                code_progress = code_lines.copy()
                frame = self.create_video_frame(scheme, day_data['day'], day_data['title'], language,
                    code_lines, output_text, code_progress, len(output_text) if output_text else 0, bool(output_text), t_val=t_val, total_duration=duration)
            frames.append(frame)
            
            # Print progress every 30 frames
            if frame_num % 30 == 0:
                print(f"   Rendering Frame {frame_num}/{total_frames}", end='\r')
        
        def make_frame(t):
            frame_idx = int(t * self.fps)
            return frames[min(frame_idx, len(frames) - 1)]
        
        video_clip = VideoClip(make_frame, duration=duration)
        video_clip = video_clip.set_audio(audio)
        return video_clip

    def generate_youtube_metadata(self, day_data):
        """Generates viral, dynamic metadata using Gemini AI or fallback templates."""
        language = day_data.get('language', 'python')
        language_name = self.language_names.get(language, language.capitalize())
        
        if self.has_ai:
             current_date_str = datetime.now().strftime("%B %Y")
             prompt = f"""
             You are a YouTube viral marketing expert. Generate metadata for a YouTube Short.
             
             CONTEXT:
             - Date: {current_date_str} (Use this for trending/seasonal tags)
             - TOPIC: Day {day_data['day']} - {day_data['title']}
             LANGUAGE/CATEGORY: {language_name}
             EXPLANATION: {day_data.get('explanation', '')}
             CONTENT SNIPPET: {day_data['code']}
             
             REQUIREMENTS:
             1. TITLE: EXTREME CLICKBAIT, under 100 chars. MUST include #shorts #viral. Use CAPS and Emojis (e.g. "STOP DOING THIS! 🛑").
             2. DESCRIPTION: High energy. Start with a hook. Use bullet points for readability. Include MANY emojis. Mention "Day {day_data['day']}".
                Explain the content simply but dramatically. End with strong CTA.
                **IMPORTANT: End the description with a block of 5-10 trending hashtags like #shorts #viral #coding #python #learntocode etc.**
             3. TAGS: Comma-separated list of 15-20 high-ranking tags.
                - MUST include broad viral tags (e.g. #fyp, #trending).
                - MUST include niche specific tags (e.g. #{language}, #coding).
                - MUST include TIME-SENSITIVE tags relevant to {current_date_str} (e.g. if it's January, maybe #newyearcoding, #2026goals).
                - Ensure the mix optimizes for BOTH Search and Browse features.
             
             OUTPUT FORMAT (JSON):
             {{
                 "title": "string",
                 "description": "string",
                 "tags": ["tag1", "tag2"]
             }}
             """
             
             # Direct Generation (with Auto-Fallback)
             try:
                 response = self.genai_model.generate_content(prompt)
             except Exception as e:
                 print(f"⚠️ Primary Model Generation Failed: {e}")
                 print("🔄 Switching to Fallback Model: gemini-pro")
                 import google.generativeai as genai
                 self.genai_model = genai.GenerativeModel('gemini-pro')
                 response = self.genai_model.generate_content(prompt)

             cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
             ai_data = json.loads(cleaned_text)
             
             # Enforce mandatory tags in TITLE
             title = ai_data.get('title', '')
             if "#shorts" not in title.lower(): title += " #shorts"
             if "#viral" not in title.lower(): title += " #viral"
             
             # Sanitize Title
             title = title.replace("<", "").replace(">", "")
             
             # Enforce mandatory hashtags in DESCRIPTION
             description = ai_data.get('description', '')
             mandatory_hashtags = "\n\n#shorts #viral #coding #programming #learntocode #tech #developer"
             if "#shorts" not in description.lower():
                 description += mandatory_hashtags
                 
             # Sanitize Description - Remove patterns YouTube rejects
             import re
             # Remove any URL-like patterns (YouTube rejects certain URL formats)
             description = re.sub(r'https?://[^\s]+', '', description)
             description = re.sub(r'www\.[^\s]+', '', description)
             # Remove angle brackets and HTML-like patterns
             description = re.sub(r'<[^>]*>', '', description)
             description = description.replace("<", "").replace(">", "")
             # Remove excessive special characters that might cause issues
             description = re.sub(r'[<>{}|\[\]\\^`]', '', description)
             # Clean up any resulting double spaces or excessive newlines
             description = re.sub(r' +', ' ', description)
             description = re.sub(r'\n{3,}', '\n\n', description)
             
             print(f"   Generated Title: {title}")
             print(f"   Generated Description Length: {len(description)}")
             
             return {
                 "title": title[:100], 
                 "description": description[:5000],  # Ensure within limit
                 "tags": ai_data.get('tags', []), 
                 "category": "27", 
                 "privacyStatus": "public"
             }
        else:
             print("❌ AI Model missing but Fallback disabled by user request. Exiting.")
             raise Exception("AI Model Required for Trending Metadata")

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

        # LAUNCH GUARD: Skip runs on Jan 6th 2026 (User requested start from the 7th)
        if datetime.now().strftime('%Y-%m-%d') == '2026-01-06':
             print("🛑 Skipping run (Launch starts Jan 7th).")
             return
        
        print(f"\n{'='*50}")
        print(f"🔥 Processing Day {day_data['day']}: {day_data['title']}")
        print(f"{'='*50}")
        
        # Dynamic Theme Generation
        print("🎨 Generating Dynamic Theme...")
        scheme = self.generate_dynamic_theme(day_data['title'])
        print(f"   Theme: {scheme.get('name', 'custom')}")
        
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
            print("❌ Upload failed. See logs for details.")
            raise Exception("YouTube Upload Failed - Action Failed to Alert User")

if __name__ == "__main__":
    automation = YouTubeAutomation()
    automation.run_daily_automation("content.json")
