from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import requests
import os
import lyricsgenius
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import APIRouter, Request
from backend.routes.emotion_route import router as emotion_router
from backend.emotion_analyzer import analyze_emotions
from backend.routes import summary_route
from backend.routes.chord_router import router as chord_router
from backend.routes.artist_info_router import router as artist_info_router



router = APIRouter()

# Load environment variables
load_dotenv()

GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

headers = {
    "Authorization": f"Bearer {GENIUS_API_TOKEN}",
    "User-Agent": "Mozilla/5.0"
}

# Setup OpenAI (NVIDIA NIM endpoint)
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

app = FastAPI()
app.include_router(emotion_router)
app.include_router(summary_route.router)
app.include_router(chord_router)
app.include_router(artist_info_router)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SongRequest(BaseModel):
    title: str
    artist: str

class LineRequest(BaseModel):
    line: str

def clean_text(text: str) -> str:
    import re
    text = re.sub(r'\*\*+', '', text)  # remove markdown bold
    text = re.sub(r'#+', '', text)     # remove markdown headers
    text = text.replace("\\n", "\n").replace("\\", "")
    return text.strip()

def fetch_lyrics_and_annotations(title, artist=None):
    headers = {
        "Authorization": f"Bearer {GENIUS_API_TOKEN}"
    }
    query = f"{title} {artist}" if artist else title
    print(f"🔍 Searching Genius for: {query}")

    try:
        search_url = f"https://api.genius.com/search?q={requests.utils.quote(query)}"

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None, None, f"Genius API error: {response.status_code}"

        hits = response.json().get("response", {}).get("hits", [])
        if not hits:
            return None, None, "No results found"

        song_data = hits[0]["result"]
        genius_title = song_data["title"]
        genius_artist = song_data["primary_artist"]["name"]
        genius_url = song_data["url"]  # ✅ Get the Genius song URL

        print(f"🎯 Matched: {genius_title} by {genius_artist}")

        genius = lyricsgenius.Genius(GENIUS_API_TOKEN, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"])
        song = genius.search_song(genius_title, genius_artist)

        if not song:
            return None, None, "LyricsGenius failed to fetch lyrics"

        return song.lyrics, genius_url, None  # ✅ Return lyrics and URL

    except Exception as e:
        return None, None, str(e)
    
def fetch_audio_preview(title, artist):
    try:
        query = f"{title} {artist}"
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&limit=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                result = results[0]
                return result.get("previewUrl"), result.get("artworkUrl100")
        return None, None
    except Exception as e:
        print(f"Preview fetch failed: {e}")
        return None, None

def explain_song_ai(title, artist, lyrics):
    system_prompt = (
    f"You are a professional music analyst. Break down the song into clearly structured, easy-to-read sections using plain text."
    f" Each section must start with a **title followed by a colon** — no markdown formatting.\n\n"
    f"Use the following section titles in this exact order:\n"
    f"- Overall Theme\n"
    f"- Emotional Tone\n"
    f"- Musical Elements (if you can guess)\n"
    f"- Psychological and Relational Insights\n"
    f"- Cultural or Societal Commentary\n"
    f"\nOnly output plain text. Avoid markdown or HTML tags. Keep each section clear and easy to read with proper line spacing.\n\n"
    f"Song Title: {title}\nArtist: {artist}\nLyrics:\n{lyrics}"
)

    completion = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.6,
        top_p=0.9,
        max_tokens=2048
    )

    return completion.choices[0].message.content

def clean_lyrics(lyrics: str) -> str:
    lines = lyrics.split("\n")
    cleaned_lines = []

    for line in lines:
        # Remove metadata tags like [Chorus], [Verse], etc.
        if line.strip().startswith("[") and line.strip().endswith("]"):
            continue

        # Skip contributor info and translations
        if any(word in line.lower() for word in ["contributors", "translations", "lyrics", "audio"]):
            continue

        # Remove empty or too-short lines
        if len(line.strip()) < 2:
            continue

        cleaned_lines.append(line.strip())

    return "\n".join(cleaned_lines)

@app.post("/explain")
async def explain_song(request: SongRequest):
    title = request.title.strip()
    artist = request.artist.strip()

    lyrics, genius_url, error = fetch_lyrics_and_annotations(title, artist)
    if not lyrics:
        return {"error": f"Genius fetch failed: {error}"}

    lyrics_clean = clean_lyrics(lyrics)

    try:
        explanation = explain_song_ai(title, artist, lyrics_clean)
        preview_url, artwork_url = fetch_audio_preview(title, artist)

        return {
            "lyrics": clean_text(lyrics_clean),
            "explanation": clean_text(explanation),
            "url": genius_url,
            "previewUrl": preview_url,
            "artwork": artwork_url  # ✅ Include artwork here
        }

    except Exception as e:
        return {"error": f"AI explanation failed: {str(e)}"}

@app.post("/explain-line")
async def explain_line(request: LineRequest):
    prompt = (
        f"You are a music analyst. Explain the meaning and emotional tone of this lyric:\n\n"
        f"{request.line}\n\n"
        f"Use plain language. Be clear and brief (2-3 sentences max)."
    )

    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.6,
            top_p=0.9,
            max_tokens=250
        )
        return {"explanation": completion.choices[0].message.content.strip()}
    except Exception as e:
        return {"explanation": f"Error: {str(e)}"}

class LinesSelection(BaseModel):
    lines: list[str]

@app.post("/explain-section")
async def explain_section(request: Request):
    body = await request.json()
    lines = body.get("lines", [])
    if not lines:
        return {"explanation": "No lines provided."}

    full_text = "\n".join(lines)
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": "Explain this selected section of song lyrics in a thoughtful, concise way. No markdown."},
                {"role": "user", "content": full_text}
            ],
            max_tokens=512
        )
        return {"explanation": response.choices[0].message.content}
    except Exception as e:
        return {"explanation": f"Failed: {str(e)}"}

class EmotionRequest(BaseModel):
    lyrics: str

@router.post("/emotion-meter")
async def emotion_meter(request: EmotionRequest):
    try:
        analysis = analyze_emotions(request.text)
        # Extract JSON object from text block
        json_start = analysis.find('{')
        json_end = analysis.rfind('}') + 1
        json_part = analysis[json_start:json_end]
        emotions = json.loads(json_part)  # ✅ Convert stringified JSON to dict
        parsed = json.loads(emotions)
        formatted = json.dumps(parsed, indent=2)
        return {"emotions": formatted}     # ✅ Return actual JSON object
    except Exception as e:
        return {"error": f"Emotion analysis failed: {str(e)}"}