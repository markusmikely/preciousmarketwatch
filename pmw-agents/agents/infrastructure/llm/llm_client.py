# Anthropic wrapper, token/cost tracking

from infrastructure.anthropic_client import AnthropicClient
from infrastructure.openai_client import OpenAIClient
from infrastructure.claude_client import ClaudeClient

class LLMClient:
    def __init__(self):
        self.anthropic = AnthropicClient()
        self.openai = OpenAIClient()
        self.claude = ClaudeClient()

    

