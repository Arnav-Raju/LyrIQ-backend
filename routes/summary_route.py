from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.lyrics_explainer import get_song_data
from backend.emotion_analyzer import analyze_emotions
from openai import OpenAI

router = APIRouter()

class SongRequest(BaseModel):
    title: str
    artist: str

@router.post("/song-summary")
async def generate_song_summary(request: SongRequest):
    try:
        # Step 1: Get song data (lyrics, explanation, etc.)
        data = get_song_data(request.title, request.artist)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        
        lyrics = data.get("lyrics", "")
        explanation = data.get("explanation", "")

        # Step 2: Analyze emotions
        emotion_data = analyze_emotions(lyrics)

        return {
            "title": request.title,
            "artist": request.artist,
            "lyrics": lyrics,
            "explanation": explanation,
            "artwork": data.get("artwork"),
            "emotions": emotion_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
