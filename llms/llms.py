# api.py
import logging
from openai import OpenAI, AsyncOpenAI
from transformers import pipeline
# from vllm import LLM, SamplingParams
import torch
import asyncio
import httpx
from contextlib import asynccontextmanager
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import openai
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


_clients = {}

@asynccontextmanager
async def get_client(base_url, api_key):
    """Get or create an AsyncOpenAI client."""
    client_key = f"{base_url}:{api_key}"
    if client_key not in _clients:
        long_timeout_async_client = httpx.AsyncClient(timeout=900)
        _clients[client_key] = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=long_timeout_async_client
        )
    try:
        yield _clients[client_key]
    finally:
        # Don't close the client here, it will be reused
        pass

def create_retry_decorator(max_retries=8, min_wait=1, max_wait=60):
    return retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            openai.RateLimitError,  # Rate limit error
            openai.APITimeoutError,  # Timeout error
            openai.APIConnectionError,  # Connection error
            openai.APIError,  # Generic API error
            asyncio.TimeoutError,  # Async timeout
            TimeoutError,  # General timeout
            ConnectionError,  # Connection issues
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"API call failed with {retry_state.outcome.exception()}, "
            f"retrying in {retry_state.next_action.sleep} seconds..."
        )
    )

@create_retry_decorator()
async def _make_api_call(client, **kwargs):
    """Helper function to make API calls with retry logic"""
    return await client.chat.completions.create(**kwargs)

def call_llm(model, prompt):
    return asyncio.run(async_call_llm(model, prompt))

async def async_call_llm(model, prompt):
    try:
        if model in ["gpt-4o-mini", "gpt-4o"]:
            api_key = "key-1234567890"
            base_url = "https://api.openai.com/v1"
            
            async with get_client(base_url, api_key) as client:
                completion = await _make_api_call(
                    client,
                    model=model,
                    store=True,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                logging.info(f"{model} API Call Successful")
                return completion.choices[0].message.content
   
        elif model in ["Llama33-70b", "Qwen2.5-14B-Instruct"]:
            async with get_client("http://localhost:8000/v1", "sk-Hello-World") as client:
                model_dict = {
                    "Llama33-70b": "meta-llama/Llama-3.3-70B-Instruct",
                    "Qwen2.5-14B-Instruct": "Qwen/Qwen2.5-14B-Instruct"
                }

                response = await _make_api_call(
                    client,
                    model=model_dict[model],
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    stream=False
                )
                logging.info(f"{model} API Call Successful")
                return response.choices[0].message.content
            
        else:
            logging.error("Unsupported model")
            return ""
            
    except Exception as e:
        logging.error(f"API Call Failed after retries: {e}")
        return ""