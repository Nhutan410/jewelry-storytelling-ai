from __future__ import annotations

import os
from openai import OpenAI
from .prompt_builder import (
    SYSTEM_PROMPT,
    ZALO_SYSTEM_PROMPT,
    CUSTOM_STORY_SYSTEM_PROMPT,
    build_user_prompt,
    build_zalo_prompt,
    build_custom_story_prompt,
)

_client: OpenAI | None = None
OPENAI_MODEL = "gpt-4o"


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY chưa được thiết lập.")
        # Giới hạn timeout và số lần retry — mặc định SDK chờ tới 600s và tự
        # retry 2 lần (kể cả lỗi quota vĩnh viễn như insufficient_quota, vốn
        # không bao giờ tự khỏi), khiến lỗi hiện ra rất chậm với người dùng.
        _client = OpenAI(api_key=api_key, timeout=45.0, max_retries=1)
    return _client


def generate_story_stream(customer: dict, product: dict, framework_key: str, temperature: float = 0.85):
    client = get_client()
    user_prompt = build_user_prompt(customer, product, framework_key)

    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=600,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def generate_zalo_stream(customer: dict, product: dict, framework_key: str, story_text: str, temperature: float = 0.80):
    client = get_client()
    user_prompt = build_zalo_prompt(customer, product, framework_key, story_text)

    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": ZALO_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=200,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def generate_custom_story_stream(inputs: dict, temperature: float = 0.82):
    client = get_client()
    user_prompt = build_custom_story_prompt(inputs)

    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": CUSTOM_STORY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=2200,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
