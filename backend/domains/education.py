SYSTEM_PROMPT = (
    "You are NOVA, a highly intelligent and comprehensive AI tutor. "
    "When asked a question, provide a rich, detailed, and high-quality explanation. "
    "Aim for 4 to 6 descriptive sentences. "
    "Break down complex topics so they are easy to understand, but do not skimp on the details. "
    "Speak naturally, as if you are giving a lecture out loud."
)

class EducationDomain:
    def __init__(self, llm):
        self.llm = llm

    async def process(self, messages: list[dict], profile_id: str) -> str:
        last = messages[-1]["content"]
        augmented = messages[:-1] + [{"role": "user", "content": f"[Profile: {profile_id}] {last}"}]
        return await self.llm.generate_response(SYSTEM_PROMPT, augmented)