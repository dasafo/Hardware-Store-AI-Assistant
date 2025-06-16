# routers/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    context: str = ""

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []

@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(request: ChatMessage):
    """
    Chat with the hardware store assistant.
    
    Args:
        request (ChatMessage): The chat request containing the message and optional context
    
    Returns:
        ChatResponse: The assistant's response and suggestions
    """
    print(f"💬 Chat message received: {request.message}")
    
    # Simple response for now - this can be enhanced with AI integration later
    message_lower = request.message.lower()
    
    # Basic keyword-based responses
    if any(word in message_lower for word in ["hola", "hello", "hi", "buenos días", "buenas tardes"]):
        response = "¡Hola! Soy tu asistente de la ferretería. ¿En qué puedo ayudarte hoy? Puedo ayudarte a buscar productos, obtener recomendaciones o responder preguntas sobre nuestro inventario."
        suggestions = [
            "Buscar martillos",
            "Recomendar herramientas eléctricas",
            "Ver productos de pintura"
        ]
    elif any(word in message_lower for word in ["buscar", "search", "encontrar", "necesito"]):
        response = "¡Perfecto! Puedo ayudarte a buscar productos. ¿Qué tipo de herramienta o material necesitas?"
        suggestions = [
            "Herramientas manuales",
            "Herramientas eléctricas",
            "Materiales de construcción",
            "Pintura y accesorios"
        ]
    elif any(word in message_lower for word in ["recomendar", "recommend", "sugerir", "similar"]):
        response = "¡Excelente! Puedo recomendarte productos similares. Si tienes un producto específico en mente, compárteme su código SKU y te mostraré opciones similares."
        suggestions = [
            "Ver productos populares",
            "Buscar por categoría",
            "Obtener recomendaciones"
        ]
    elif any(word in message_lower for word in ["precio", "cost", "costo", "cuánto"]):
        response = "Para consultar precios específicos, puedo ayudarte a encontrar los productos. Una vez que localicemos lo que necesitas, podrás ver toda la información incluyendo precios y disponibilidad."
        suggestions = [
            "Buscar producto específico",
            "Ver ofertas",
            "Comparar precios"
        ]
    else:
        response = f"Entiendo que estás consultando sobre: '{request.message}'. Puedo ayudarte a buscar productos relacionados o responder preguntas específicas sobre nuestro inventario."
        suggestions = [
            "Buscar productos relacionados",
            "Ver categorías disponibles",
            "Obtener más información"
        ]
    
    print(f"✅ Chat response generated")
    
    return ChatResponse(
        response=response,
        suggestions=suggestions
    ) 