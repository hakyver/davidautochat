# ai_app/ai_service.py
import openai
from decouple import config

class AIService:
    def __init__(self, api_key=None, model='gpt-4'):
        """
        Initialize the AIService with the API key and model.
        
        :param api_key: API key for OpenAI (optional, can also be loaded from environment variable)
        :param model: Model to be used for the chat (default is 'gpt-4')
        """
        self.api_key = api_key or config('OPENAI_API_KEY')
        self.model = model

    def create_chat(self, messages, model=None):
        """
        Create a chat completion using the OpenAI API.
        
        :param messages: List of messages to be sent to the model
        :param model: Specific model to use (optional, defaults to instance model)
        :return: The response content from the chat completion
        """
        # Use the default model if none is provided
        if model is None:
            model = self.model
        
        # Set the OpenAI API key
        openai.api_key = self.api_key
        
        # Create the chat completion
        response = openai.ChatCompletion.create(model=model, messages=messages)
        
        # Return the content of the first message in the choices
        return response['choices'][0]['message']['content']
