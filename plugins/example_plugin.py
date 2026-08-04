"""
AiChat Pro — Example Plugin
Demonstrates the plugin hook interface.
Place .py files in /plugins/ to extend the system.
"""


def on_user_message(data):
    """Called when the user sends a message. data = dict with 'content' key."""
    print(f"[ExamplePlugin] User said: {data.get('content', '')[:50]}")


def on_ai_response(data):
    """Called when the AI responds. data = dict with 'content' key."""
    print(f"[ExamplePlugin] AI replied: {data.get('content', '')[:50]}")
