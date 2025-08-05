import re
from ..LLMInterface import LLMInterface
from ..LLMEnums import LLMEnums, CohereEnums, DocumentTypeEnum
import cohere
import logging
from typing import List, Union


class CohereProvider(LLMInterface):
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
        self.client = cohere.ClientV2(api_key=self.api_key)
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = CohereEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """
        Set the model ID for text generation.
        """
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        """
        Set the model ID and embedding size for text embeddings.
        """
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str) -> str:
        """
        Process the input text to ensure it does not exceed the maximum allowed characters.
        """
        return text[: self.default_input_max_characters].strip()

    def generate_text(
        self,
        prompt: str,
        max_output_tokens: int = None,
        chat_history: list = [],
        temperature: float = None,
    ) -> str:
        """
        Generate text based on the provided prompt.
        """
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model for Cohere is not set.")
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
            self.construct_prompt(prompt=prompt, role=CohereEnums.USER.value)
        )
        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature,
        )
        if (
            not response
            or not response.message
            or not response.message.content
            or not response.message.content[0]
            or not response.message.content[0].text
        ):
            self.logger.error("Failed to generate text from Cohere.")
            return None

        return response.message.content[0].text

    def embed_text(
        self, text: Union[str, List[str]], document_type: str = None
    ) -> list:
        """
        Embed the input text using the specified model.
        """
        if isinstance(text, str):
            text = [text]
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model for Cohere is not set.")
            return None

        input_type = CohereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CohereEnums.QUERY.value

        response = self.client.embed(
            model=self.embedding_model_id,
            input_type=input_type,
            texts=[self.process_text(t) for t in text],
            embedding_types=["float"],
        )
        if response is None or not response.embeddings or not response.embeddings.float:
            self.logger.error("Failed to embed text with cohere.")
            return None

        return [f for f in response.embeddings.float]

    def construct_prompt(self, prompt: str, role: str) -> dict:
        """
        Construct a prompt string based on the role and input prompt.
        """
        return {"role": role, "content": prompt}
