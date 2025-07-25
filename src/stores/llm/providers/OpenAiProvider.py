from ..LLMInterface import LLMInterface
from ..LLMEnums import LLMEnums , OpenAiEnums
from openai import OpenAI
import logging
class OpenAiProvider(LLMInterface):
    def __init__(self, api_key: str, api_url: str = None,
                default_input_max_characters: int = 1000,
                default_output_max_tokens: int = 1000,
                default_temperature: float = 0.1):
        
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature
        self.client = OpenAI(api_key=self.api_key)

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client= OpenAI(
            api_key=self.api_key,
            api_url=self.api_url
        )
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """
        Set the model ID for text generation.
        """
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int ):
        """
        Set the model ID for text embedding.
        """
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text:str) -> str:
        """
        Process the input text to ensure it does not exceed the maximum allowed characters.
        """
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, max_output_tokens: int = None,
                    chat_history: list = [], temperature: float = None) -> str:
        """
        Generate text based on the provided prompt.
        """
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI is not set.")
            return None
        
        temperature = temperature if temperature is not None else self.default_temperature
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        chat_history.append(self.construct_prompt(prompt=prompt,role=OpenAiEnums.USER.value))

        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )
        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("Failed to generate text from OpenAI.")
            return None

        return response.choices[0].message['content']

    def embed_text(self, text: str, document_type: str = None) -> list:
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI is not set.")
            return None
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model_id
        )
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Failed to get embedding from OpenAI.")
            return None

        return response.data[0].embedding
    
    def construct_prompt(self, prompt: str, role: str) -> str:
        """
        Construct a prompt for the language model.
        """
        return {"role": role, "content": self.process_text(prompt)}

