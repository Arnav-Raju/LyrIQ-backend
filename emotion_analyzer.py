# app/emotion_analyzer.py
from openai import OpenAI
import os
from dotenv import load_dotenv

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

def analyze_emotions(text):
    system_prompt = (
    "You are an expert in emotional analysis of song lyrics. "
    "Given a passage of lyrics, analyze the dominant emotions expressed. "
    "Respond ONLY with a valid JSON object where each key is an emotion "
    "(e.g., 'Joy', 'Sadness', 'Anger') and each value is an integer percentage. "
    "Make sure percentages add up to 100. "
    "DO NOT include any explanation, comments, or formatting like code blocks. "
    "Example:\n"
    "{\"Joy\": 40, \"Sadness\": 30, \"Anger\": 30}"
)



    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=messages,
        temperature=0.2,
        top_p=0.7,
        max_tokens=512
    )

    return response.choices[0].message.content.strip()
