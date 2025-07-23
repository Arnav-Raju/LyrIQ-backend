# backend/routes/playlist_router.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
from youtubesearchpython import VideosSearch
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

class PlaylistRequest(BaseModel):
    prompt: str

@router.post("/generate-playlist")
async def generate_playlist(req: PlaylistRequest):
    base_prompt = f"""You are a playlist curator. Given the prompt: "{req.prompt}", generate a playlist of exactly 10 songs.
    
Respond in this JSON format:
[
  {{ "title": "Song Title", "artist": "Artist Name" }},
  ...
]
Return only the JSON array.
"""

    try:
        response = openai.ChatCompletion.create(
            model="meta/llama-3.1-405b-instruct",
            messages=[{"role": "user", "content": base_prompt}],
            temperature=0.8,
            max_tokens=1000,
        )

        text = response['choices'][0]['message']['content'].strip()

        import json
        songs = json.loads(text)

        # Search YouTube URLs
        for song in songs:
            query = f"{song['title']} {song['artist']}"
            try:
                search = VideosSearch(query, limit=1)
                result = search.result()
                if result['result']:
                    song["youtubeUrl"] = result['result'][0]['link']
                else:
                    song["youtubeUrl"] = ""
            except Exception:
                song["youtubeUrl"] = ""

    except Exception:
            song["youtubeUrl"] = ""

