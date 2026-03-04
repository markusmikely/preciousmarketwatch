# Anthropic wrapper, token/cost tracking

from agents.infrastructure.anthropic_client import AnthropicClient
from agents.infrastructure.openai_client import OpenAIClient
from agents.infrastructure.claude_client import ClaudeClient

class LLMClient:
    def __init__(self):
        self.anthropic = AnthropicClient()
        self.openai = OpenAIClient()
        self.claude = ClaudeClient()

    

