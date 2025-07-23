from openai import OpenAI
import os

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

def get_song_data(title, artist):
    prompt = f"""Fetch the full lyrics of the song titled "{title}" by {artist}.
Then, provide a deep lyrical analysis, breaking down the theme, tone, message, and metaphors.

Return the result as a JSON like:
{{
    "lyrics": "...",
    "explanation": "...",
    "artwork": "https://link.to.artwork",
    "previewUrl": "https://link.to.preview"
}}"""

    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1024
    )

    try:
        content = response.choices[0].message.content.strip()
        return eval(content)  # If response is strict JSON, use `json.loads(content)` instead
    except Exception as e:
        return {"error": str(e)}
