from openai import OpenAI
import os


_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def call_llm(prompt: str) -> str:
    """
    Roept het LLM aan en retourneert RUWE tekstoutput.
    GEEN parsing. GEEN JSON-validatie. Engine doet dat.
    """
    client = _get_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text.strip()
