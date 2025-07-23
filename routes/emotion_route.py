# app/routes/emotion_route.py
import json
from fastapi import APIRouter
from pydantic import BaseModel
from backend.emotion_analyzer import analyze_emotions
from backend.schemas.emotion_request import EmotionRequest

router = APIRouter()

class EmotionRequest(BaseModel):
    lyrics: str

@router.post("/emotion-meter")
async def emotion_meter(request: EmotionRequest):
    try:
        result = analyze_emotions(request.lyrics)
        parsed = json.loads(result)
        formatted = json.dumps(parsed, indent=2)
        return {"emotions": formatted}
    except Exception as e:
        return {"error": f"Emotion analysis failed: {str(e)}"}
