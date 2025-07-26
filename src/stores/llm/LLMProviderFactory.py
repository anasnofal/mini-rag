from openai import api_key
from .providers import CohereProvider
from .providers import OpenAiProvider
from helpers.config import Settings
from .LLMEnums import LLMEnums

class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config

    def create(self, provider: str ) :
        if provider == LLMEnums.OPENAI.value:
            return OpenAiProvider(
                api_key== self.config.OpenAI_API_KEY,
                api_url=self.config.OPENAI_API_URL,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        if provider == LLMEnums.COHERE.value:
            return CohereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        return None
    

