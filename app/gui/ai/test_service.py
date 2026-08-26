from app.gui.ai.service import AIService

ai = AIService()

print("AI SERVICE TEST")
print("Ready:", ai.is_ready())
print(ai.analyze("Test Pixel device log"))
