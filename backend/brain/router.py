import re
from backend.brain.llm_client import LLMClient


HOME_PATTERN = re.compile(
    r'\b(turn\s+(on|off)|switch|dim|set|control|adjust)\b.*'
    r'\b(light|fan|plug|thermostat|ac|heater|bedroom|kitchen|living\s+room|tv)\b'
    r'|\b(light|fan|thermostat|ac)\b.*\b(turn|switch|dim|set)\b',
    re.IGNORECASE,
)

INTENT_PROMPT = (
    "You are an intent classifier. Reply with exactly one word: "
    "'education' or 'home'.\n"
    "'home' means controlling smart home devices.\n"
    "'education' means anything else — learning, Q&A, coding, quizzes, advice.\n"
    "Text: "
)


class IntentRouter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def classify(self, text: str) -> str:
        if HOME_PATTERN.search(text):
            return "home"
        result = await self.llm.generate_response(
            INTENT_PROMPT,
            [{"role": "user", "content": text}],
        )
        word = result.strip().lower().split()[0]
        return word if word in ("home", "education") else "education"