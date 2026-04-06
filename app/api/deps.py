from app.services.ai_service import AIService
from app.core.config import settings

def get_ai_service():
    return AIService(api_key=settings.GEMINI_API_KEY, model_id=settings.MODEL_ID)