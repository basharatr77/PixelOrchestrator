class AIService:
    """Safe AI service boundary for PixelOrchestrator."""

    def __init__(self):
        self.provider = None

    def is_ready(self):
        return self.provider is not None

    def analyze(self, text: str) -> str:
        if not text.strip():
            return "Please provide something to analyze."

        return "AI service is ready. Provider connection will be added next."
