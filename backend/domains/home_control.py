SYSTEM_PROMPT = (
    "You are NOVA, a smart home controller. "
    "Confirm actions in ONE short sentence only. "
    "Maximum 15 words in your response. "
    "Example: 'Turning off bedroom lights.' "
    "If unauthorized, say why in one sentence."
)

PERMISSIONS: dict[str, list[str]] = {
    "kids": ["living room", "thermostat", "front door"],
    "dad":  [],
    "mom":  [],
}


class HomeControlDomain:
    def __init__(self, llm):
        self.llm = llm

    async def process(self, messages: list[dict], profile_id: str) -> str:
        text = messages[-1]["content"].lower()
        blocked = PERMISSIONS.get(profile_id, [])

        if any(b in text for b in blocked):
            return (
                f"Sorry {profile_id}, "
                f"you don't have permission to control that."
            )

        response = await self.llm.generate_response(
            SYSTEM_PROMPT, messages[-1:]
        )
        await self._dispatch(text)
        return response

    async def _dispatch(self, command: str):
        # Uncomment below and add HA_WEBHOOK_URL to .env to go live
        # async with httpx.AsyncClient(timeout=5) as client:
        #     await client.post(settings.ha_webhook_url,
        #                       json={"command": command})
        print(f"[Home Action]: {command}")