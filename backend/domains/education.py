SYSTEM_PROMPT = (
    "You are ZEUS, an expert AI tutor. "
    "Help with math, science, history, English, and coding. "
    "Generate quizzes, flashcards, and clear explanations. "
    "Be concise — under 120 words unless the user asks to elaborate. "
    "If giving a quiz, number the questions clearly."
)


class EducationDomain:
    def __init__(self, llm):
        self.llm = llm

    async def process(self, messages: list[dict], profile_id: str) -> str:
        last = messages[-1]["content"]
        augmented = messages[:-1] + [
            {"role": "user", "content": f"[Profile: {profile_id}] {last}"}
        ]
        return await self.llm.generate_response(SYSTEM_PROMPT, augmented)