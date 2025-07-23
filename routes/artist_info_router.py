from fastapi import APIRouter, Query
import requests
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")

# Get Spotify token
def get_spotify_token():
    url = 'https://accounts.spotify.com/api/token'
    res = requests.post(url, data={'grant_type': 'client_credentials'}, auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
    return res.json().get("access_token")

# Get artist info
@router.get("/artist-info")
def get_artist_info(artist_name: str):
    spotify_token = get_spotify_token()
    headers = {"Authorization": f"Bearer {spotify_token}"}
    
    # 1. Search artist
    search_url = f"https://api.spotify.com/v1/search"
    params = {"q": artist_name, "type": "artist", "limit": 1}
    artist_data = requests.get(search_url, headers=headers, params=params).json()
    artist_items = artist_data.get("artists", {}).get("items", [])
    if not artist_items:
        return {"error": "Artist not found"}

    artist = artist_items[0]
    artist_id = artist["id"]
    artist_images = artist.get("images", [])
    
    # 2. Get top tracks
    top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    tracks_data = requests.get(top_tracks_url, headers=headers, params={"market": "US"}).json()
    top_songs = [{"name": t["name"], "preview_url": t["preview_url"]} for t in tracks_data.get("tracks", [])[:3]]

    # 3. Get albums
    albums_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    albums_data = requests.get(albums_url, headers=headers, params={"include_groups": "album", "limit": 5}).json()
    sorted_albums = sorted(albums_data.get("items", []), key=lambda x: x.get("popularity", 0), reverse=True)
    top_album = sorted_albums[0] if sorted_albums else None

    # 4. Genius Bio
    genius_headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    genius_search = requests.get("https://api.genius.com/search", headers=genius_headers, params={"q": artist_name}).json()
    hit = genius_search["response"]["hits"][0]["result"] if genius_search["response"]["hits"] else None
    genius_artist_id = hit["primary_artist"]["id"] if hit else None

    bio = "Biography not found."
    if genius_artist_id:
        artist_url = f"https://genius.com/artists/{genius_artist_id}"
        bio = f"Read more at Genius: {artist_url}"

    return {
        "name": artist["name"],
        "bio": bio,
        "topSongs": top_songs,
        "popularAlbum": {
            "title": top_album["name"],
            "year": top_album["release_date"][:4],
            "cover": top_album["images"][0]["url"] if top_album["images"] else "",
            "genre": "Unknown"
        } if top_album else None,
        "images": [img["url"] for img in artist_images[:3]]
    }
