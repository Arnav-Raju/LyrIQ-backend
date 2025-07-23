from fastapi import APIRouter, Request
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re

router = APIRouter()

class ChordRequest(BaseModel):
    title: str
    artist: str
    lyrics: str | None = None  # Not used, but included for compatibility

def slugify(text):
    return re.sub(r"[^\w\s-]", "", text).lower().strip().replace(" ", "-")

@router.post("/generate-chords")
def generate_chords(data: ChordRequest):
    song_slug = slugify(data.title)
    artist_slug = slugify(data.artist)
    url = f"https://www.amchords.com/piano/{artist_slug}/{song_slug}"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return {"error": f"AmChords returned status code {res.status_code}"}

        soup = BeautifulSoup(res.text, "html.parser")
        pre_tag = soup.find("pre")
        if not pre_tag:
            return {"error": "Chords block not found on AmChords"}

        chords = pre_tag.get_text(separator="\n").strip()
        return {"chords": chords}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
