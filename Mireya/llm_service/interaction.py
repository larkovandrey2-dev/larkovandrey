import aiohttp
import asyncio
import os
from typing import Optional, Dict, List, Union
from dotenv import load_dotenv
import hashlib
from llm_service.prompts import (
    get_analysis_prompt,
    get_follow_up_generation_prompt,
    get_follow_up_template,
    reset_follow_up_tracking,
    get_rephrase_prompt
)

load_dotenv()

YC_API_TOKEN = os.getenv('YC_API_TOKEN')
MODEL_URI = "gpt://b1gcbn4fh3ils5usalqv/yandexgpt-5.1/latest"
HEADERS = {
    "Authorization": f"Bearer {YC_API_TOKEN}",
    "Content-Type": "application/json"
}

# In-memory cache for LLM responses
_prompt_cache: Dict[str, str] = {}
_cache_max_size = 200

# Track last follow-up questions to avoid repetition
_last_follow_ups: Dict[int, List[str]] = {}
_max_tracked_follow_ups = 5


def _get_cache_key(question: str, answer: str) -> str:
    """Generate cache key for prompt."""
    return hashlib.md5(f"{question}:{answer}".encode()).hexdigest()


async def _ask_model_async(
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 150,
    timeout: int = 30
) -> Optional[Dict]:
    """Async call to Yandex GPT API with optimized settings."""
    data = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "temperature": temperature,
            "maxTokens": str(max_tokens)
        },
        "messages": [
            {"role": "user", "text": prompt}
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers=HEADERS,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"LLM API error {response.status}: {error_text}")
                    return None
    except aiohttp.ClientError as e:
        print(f"LLM API error: {e}")


async def diversify_question(question_text: str) -> str:
    """
    Takes an original question and returns a rephrased version
    using LLM to make it sound more natural/varied.
    """
    if len(question_text) < 5:
        return question_text
    prompt = get_rephrase_prompt(question_text)
    api_response = await _ask_model_async(prompt, temperature=0.8, max_tokens=150)

    if not api_response:
        return question_text

    try:
        new_text = api_response['result']['alternatives'][0]['message']['text'].strip()

        if ":" in new_text[:20]:
            new_text = new_text.split(":", 1)[1].strip()

        new_text = new_text.replace('"', '').replace("«", "").replace("»", "")
        if len(new_text) < 5:
            return question_text

        return new_text

    except (KeyError, IndexError):
        return question_text
async def analyze_question(
    question: str,
    question_n: int,
    answer: str,
    last_json: Optional[Dict[int, int]] = None,
    attempt: int = 0,
    survey_n: int = 1
) -> Union[Dict[int, int], List]:
    """
    Analyze user answer and return score or follow-up question.
    Returns either updated last_json dict or [-1, follow_up_question].
    Ensures follow-up questions never repeat.
    """

    if last_json is None:
        last_json = {}
    
    # Get varied analysis prompt
    prompt = get_analysis_prompt(question, answer, question_n, survey_n)
    
    # Check cache
    cache_key = _get_cache_key(question, answer)
    if cache_key in _prompt_cache:
        response_text = _prompt_cache[cache_key]
    else:
        api_response = await _ask_model_async(prompt, temperature=0.0, max_tokens=50)
        if not api_response:
            return last_json
        
        try:
            response_text = api_response['result']['alternatives'][0]['message']['text'].strip()
        except (KeyError, IndexError):
            return last_json
        
        # Cache result
        if len(_prompt_cache) >= _cache_max_size:
            # Clear 50% of cache
            keys_to_remove = list(_prompt_cache.keys())[:_cache_max_size // 2]
            for key in keys_to_remove:
                _prompt_cache.pop(key, None)
        _prompt_cache[cache_key] = response_text
    
    # Parse response
    if response_text == '-1' or not response_text.isdigit():
        # Generate follow-up question with anti-repetition logic
        follow_up_question = await _generate_unique_follow_up(
            question, question_n, attempt
        )
        return [-1, follow_up_question]
    
    try:
        score = int(response_text)
        if 0 <= score <= 3:
            last_json[question_n] = score
            # Reset follow-up tracking when we get a valid answer
            reset_follow_up_tracking(question_n)
    except ValueError:
        pass
    
    return last_json


async def _generate_unique_follow_up(
    original_question: str,
    question_n: int,
    attempt: int = 0
) -> str:
    """Generate a follow-up question that hasn't been used recently."""
    # Initialize tracking for this question
    if question_n not in _last_follow_ups:
        _last_follow_ups[question_n] = []
    
    used = _last_follow_ups[question_n]
    
    # Try to generate via LLM first
    generation_prompt = get_follow_up_generation_prompt(original_question, attempt)
    llm_response = await _ask_model_async(
        generation_prompt,
        temperature=0.4 + (attempt * 0.1),  # Increase creativity with attempts
        max_tokens=120
    )
    
    if llm_response:
        try:
            follow_up_text = llm_response['result']['alternatives'][0]['message']['text'].strip()
            # Clean up response
            follow_up_text = follow_up_text.strip('"\'«»').split('\n')[0].strip()
            
            # Check if we've used this before
            if follow_up_text not in used:
                # Track it
                used.append(follow_up_text)
                if len(used) > _max_tracked_follow_ups:
                    used.pop(0)
                
                # Ensure length
                if len(follow_up_text) > 100:
                    follow_up_text = follow_up_text[:97] + "..."
                elif len(follow_up_text) < 30:
                    # Too short, use template
                    pass
                else:
                    return follow_up_text
        except (KeyError, IndexError):
            pass
    
    # Fallback to template system with anti-repetition
    max_attempts = 10
    for _ in range(max_attempts):
        template_text = get_follow_up_template(original_question, question_n, attempt)
        
        # Check if we've used this exact text
        if template_text not in used:
            used.append(template_text)
            if len(used) > _max_tracked_follow_ups:
                used.pop(0)
            return template_text
        
        attempt += 1
    
    # Last resort: return template even if used (shouldn't happen)
    return get_follow_up_template(original_question, question_n, attempt)
