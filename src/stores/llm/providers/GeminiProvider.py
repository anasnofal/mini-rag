from urllib import response
from ..LLMInterface import LLMInterface
from ..LLMEnums import DocumentTypeEnumGemini, LLMEnums, GeminiEnums, DocumentTypeEnum
from google import genai
from google.genai import types
import logging
from typing import Union, List


class GeminiProvider(LLMInterface):
    def __init__(
        self,
        api_key: str,
        default_input_max_characters: int = 1000,
        default_output_max_tokens: int = 1000,
        default_temperature: float = 0.1,
    ):
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature
        self.client = genai.Client(api_key=self.api_key)
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = GeminiEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """Set the model ID for text generation."""
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        """Set the model ID and embedding size for text embeddings."""
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str) -> str:
        """
        Process the input text to ensure it does not exceed the maximum allowed characters,
        and strip whitespace after truncation.
        """
        return text[: self.default_input_max_characters].strip()

    def generate_text(
        self,
        prompt: str,
        max_output_tokens: int = None,
        chat_history: list = [],
        temperature: float = None,
    ) -> str:
        """Generate text based on the provided prompt."""
        if not self.client:
            self.logger.error("Gemini client is not initialized.")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini is not set.")
            return None

        temperature = (
            temperature if temperature is not None else self.default_temperature
        )
        max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_output_max_tokens
        )
        chat_history.append(
            self.construct_prompt(prompt=prompt, role=GeminiEnums.USER.value)
        )

        response = self.client.models.generate_content(
            model=self.generation_model_id,
            contents=chat_history,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            ),
        )

        if not response or not response.text:
            self.logger.error("Failed to generate text.")
            return None
        response_text = response.__dict__
        print(response_text)
        return response_text.candidates[0].content.parts[0].text

    def construct_prompt(self, prompt: str, role: str):
        """
        Construct a prompt for the Gemini language model.

        Args:
            prompt (str): The input text prompt to be sent to the model.
            role (str): The role of the message sender (e.g., 'user' or 'assistant').

        Returns:
            types.Content: A Content object with the specified role and a single Part containing the processed prompt text.
                This object is intended to be used as input for the Gemini model's content generation methods.
        """
        return types.Content(role=role, parts=[types.Part(text=prompt)])

    def embed_text(self, text: Union[str, List[str]], document_type: str) -> list:
        """Generate embeddings for the provided text."""
        if not self.client:
            self.logger.error("Gemini client is not initialized.")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini is not set.")
            return None
        if document_type == DocumentTypeEnum.DOCUMENT.value:
            document_type = DocumentTypeEnumGemini.RETRIEVAL_DOCUMENT.value
        response = self.client.models.embed_content(
            model=self.embedding_model_id,
            contents=text,
            config=types.EmbeddingConfig(task_type=document_type),
        )

        if not response or not response.embeddings or len(response.embeddings) == 0:
            self.logger.error("Failed to get embedding from Gemini.")
            return None
        return [f.values for f in response.embeddings]
