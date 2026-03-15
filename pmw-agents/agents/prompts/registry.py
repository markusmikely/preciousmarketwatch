# agents/prompts/__init__.py
# agents/prompts/registry.py

import json
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).parent / "templates"

class PromptRegistry:
    """Loads and renders prompt templates from YAML/JSON files."""
    
    _cache: dict[str, dict] = {}
    
    @classmethod
    def get(cls, template_key: str) -> dict:
        """Return {"system": str, "user": str} for the given key."""
        if template_key not in cls._cache:
            path = PROMPT_DIR / f"{template_key}.json"
            if not path.exists():
                raise FileNotFoundError(f"Prompt template not found: {template_key}")
            cls._cache[template_key] = json.loads(path.read_text())
        return cls._cache[template_key]
    
    @classmethod
    def render(cls, template_key: str, variables: dict) -> str:
        """Load template and substitute {{VAR}} placeholders."""
        tmpl = cls.get(template_key)
        system = tmpl.get("system", "")
        user = tmpl.get("user", "")
        
        for key, value in variables.items():
            placeholder = "{{" + key.upper() + "}}"
            system = system.replace(placeholder, str(value))
            user = user.replace(placeholder, str(value))
        
        return f"{system}\n\n{user}"