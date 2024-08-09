from .utils import get_history_parse, handle_history
from .ai_service import AIService

def conversational_layer(state):
    """
    This function handles the conversational layer of the AI interaction.
    It retrieves the conversation history, processes it with AI, and updates the state.
    """
    # Parse the conversation history from the state
    history = get_history_parse(state)
    
    # Initialize the AI service
    ai = AIService()
    
    # Create a chat prompt for the conversational layer
    response = ai.create_chat([
        {'role': 'system', 'content': 'Conversational layer initiated.'},
        {'role': 'user', 'content': history}
    ])
    
    # Update the conversation history in the state
    handle_history(response, state)
    
    return response

def main_layer(state):
    """
    This function handles the main layer of the AI interaction.
    It processes the state with AI and updates the state with the new response.
    """
    # Initialize the AI service
    ai = AIService()
    
    # Create a chat prompt for the main layer
    response = ai.create_chat([
        {'role': 'system', 'content': 'Main layer processing.'},
        {'role': 'user', 'content': state.get('history', '')}
    ])
    
    # Update the conversation history in the state
    handle_history(response, state)
    
    return response

