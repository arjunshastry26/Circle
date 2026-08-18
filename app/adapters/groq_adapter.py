from .openai_adapter import OpenAIAdapter


class GroqAdapter(OpenAIAdapter):
    """
    Groq's API is OpenAI-compatible, so no new translation logic is needed -
    this is exactly the point of standardizing on one schema. Kept as its
    own class (rather than just reusing OpenAIAdapter directly in the
    routing table) so the base_url/api_key wiring stays per-provider and
    it's obvious where to add provider-specific quirks later if Groq's API
    ever diverges.
    """

    pass
