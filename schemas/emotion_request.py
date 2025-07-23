from pydantic import BaseModel

class EmotionRequest(BaseModel):
    lyrics: str
