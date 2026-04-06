import re
from backend.brain.llm_client import LLMClient

HOME_PATTERN = re.compile(
    r'\b(turn\s+(on|off)|switch|dim|set|control|adjust)\b.*'
    r'\b(light|fan|plug|thermostat|ac|heater|bedroom|kitchen|living\s+room|tv)\b',
    re.IGNORECASE,
)

INTENT_PROMPT = "You classify text. Reply with exactly one word: 'home' or 'education'. Text: "

class IntentRouter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def classify(self, text: str) -> str:
        if HOME_PATTERN.search(text): return "home"
        result = await self.llm.generate_response(INTENT_PROMPT, [{"role": "user", "content": text}])
        word = result.strip().lower().split()[0]
        return word if word in ("home", "education") else "education"