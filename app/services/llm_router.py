import os
from app.services import llm_cache


async def generate(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    use_cache: bool = True,
) -> str:
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    # Chat messages are unique per session — skip cache to preserve conversational flow
    if use_cache:
        cached = await llm_cache.get(provider, model, system_prompt, user_message)
        if cached:
            return cached

    if provider == "openai":
        result = await _generate_openai(system_prompt, user_message, temperature, max_tokens)
    elif provider == "anthropic":
        result = await _generate_anthropic(system_prompt, user_message, temperature, max_tokens)
    elif provider == "gemini":
        result = await _generate_gemini(system_prompt, user_message, temperature, max_tokens)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

    if use_cache:
        await llm_cache.set(provider, model, system_prompt, user_message, result)

    return result


async def _generate_openai(
    system_prompt: str, user_message: str, temperature: float, max_tokens: int
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def _generate_anthropic(
    system_prompt: str, user_message: str, temperature: float, max_tokens: int
) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-6")

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


async def _generate_gemini(
    system_prompt: str, user_message: str, temperature: float, max_tokens: int
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    response = await model.generate_content_async(
        user_message,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text
