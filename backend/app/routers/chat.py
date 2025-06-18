# routers/chat.py

from fastapi import APIRouter
from app.models.product import ChatRequest, ChatFullResponse, ChatResponse, ChatMetadata, ChatSuggestion, Product
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_skus
from datetime import datetime
import re
from pydantic import BaseModel
from app.utils.logger import logger, log_with_context
from typing import Union
from app.services.openai_service import get_openai_service

router = APIRouter()

def analyze_user_intent(message: str):
    """
    Analyze user message to determine intent and extract keywords.
    """
    message_lower = message.lower()
    
    # Define intent patterns
    search_patterns = [
        r'busco?\s+(.+)', r'necesito\s+(.+)', r'quiero\s+(.+)', 
        r'me\s+interesa\s+(.+)', r'estoy\s+buscando\s+(.+)',
        r'donde\s+encuentro\s+(.+)', r'tienen\s+(.+)'
    ]
    
    greeting_patterns = [
        r'hola', r'buenos?\s+d[íi]as?', r'buenas?\s+tardes?', 
        r'buenas?\s+noches?', r'saludos?'
    ]
    
    help_patterns = [
        r'ayuda', r'help', r'no\s+s[ée]\s+qu[ée]', r'qu[ée]\s+puedo',
        r'c[óo]mo\s+funciona', r'qu[ée]\s+tienen'
    ]
    
    # Check for search intent
    for pattern in search_patterns:
        match = re.search(pattern, message_lower)
        if match:
            return "search", match.group(1).strip()
    
    # Check for greeting
    for pattern in greeting_patterns:
        if re.search(pattern, message_lower):
            return "greeting", None
    
    # Check for help
    for pattern in help_patterns:
        if re.search(pattern, message_lower):
            return "help", None
    
    # Default to search with full message
    return "search", message_lower

def generate_chat_response(intent: str, keywords: str, products: list):
    """
    Generate appropriate chat response based on intent and found products.
    """
    if intent == "greeting":
        return {
            "response": "¡Hola! Bienvenido a nuestra ferretería. ¿En qué puedo ayudarte hoy?",
            "suggestions": [
                ChatSuggestion(text="Buscar herramientas", action="search", value="herramientas"),
                ChatSuggestion(text="Ver categorías", action="category", value="all"),
                ChatSuggestion(text="Productos populares", action="search", value="popular"),
                ChatSuggestion(text="Ayuda", action="help", value=None)
            ]
        }
    
    elif intent == "help":
        return {
            "response": "Puedo ayudarte a encontrar productos en nuestra ferretería. Puedes buscar por nombre, categoría o describir lo que necesitas.",
            "suggestions": [
                ChatSuggestion(text="Herramientas manuales", action="search", value="herramientas manuales"),
                ChatSuggestion(text="Herramientas eléctricas", action="search", value="herramientas electricas"),
                ChatSuggestion(text="Materiales de construcción", action="search", value="materiales construccion"),
                ChatSuggestion(text="Pintura y accesorios", action="search", value="pintura")
            ]
        }
    
    elif intent == "search":
        if products:
            product_names = [p['name'] for p in products[:3]]
            response = f"Encontré {len(products)} productos relacionados con '{keywords}'. "
            if len(products) > 3:
                response += f"Los principales son: {', '.join(product_names)} y más."
            else:
                response += f"Aquí tienes: {', '.join(product_names)}."
            
            suggestions = []
            # Add suggestions based on found products
            for product in products[:3]:
                suggestions.append(
                    ChatSuggestion(
                        text=f"Ver {product['name']}", 
                        action="product", 
                        value=product['sku']
                    )
                )
            
            # Add related search suggestions
            suggestions.append(
                ChatSuggestion(text="Buscar similares", action="search", value=f"similar {keywords}")
            )
            
            return {
                "response": response,
                "suggestions": suggestions
            }
        else:
            return {
                "response": f"No encontré productos específicos para '{keywords}', pero puedo ayudarte con otras opciones.",
                "suggestions": [
                    ChatSuggestion(text="Herramientas", action="search", value="herramientas"),
                    ChatSuggestion(text="Materiales", action="search", value="materiales"),
                    ChatSuggestion(text="Pintura", action="search", value="pintura"),
                    ChatSuggestion(text="Ver todo", action="category", value="all")
                ]
            }
    
    return {
        "response": "¿En qué puedo ayudarte?",
        "suggestions": [
            ChatSuggestion(text="Buscar productos", action="search", value=""),
            ChatSuggestion(text="Ver categorías", action="category", value="all")
        ]
    }

@router.post("/chat", response_model=ChatFullResponse)
def chat_with_assistant(payload: ChatRequest):
    """
    Intelligent chat endpoint that processes user queries and provides contextual responses.
    
    Args:
        payload (ChatRequest): The chat request containing the user's message
    
    Returns:
        ChatFullResponse: Intelligent response with suggestions and relevant products
    """
    message = payload.message.strip()
    print(f"💬 Processing chat message: '{message}'")
    
    # Analyze user intent
    intent, keywords = analyze_user_intent(message)
    print(f"🎯 Detected intent: {intent}, keywords: {keywords}")
    
    # Search for products if intent is search
    products = []
    if intent == "search" and keywords:
        try:
            # Generate embedding and search
            embedding = get_embedding(keywords)
            skus = search_in_qdrant(embedding, top_k=5)
            products = get_products_by_skus(skus)
            print(f"🔍 Found {len(products)} products for search")
        except Exception as e:
            print(f"⚠️ Error searching products: {str(e)}")
            products = []
    
    # Generate response
    chat_data = generate_chat_response(intent, keywords, products)
    
    # Create response objects
    chat_response = ChatResponse(
        response=chat_data["response"],
        suggestions=chat_data["suggestions"],
        products=[Product(**p) for p in products[:3]]  # Include top 3 products
    )
    
    metadata = ChatMetadata(
        timestamp=datetime.utcnow().isoformat() + "Z",
        response_type=intent,
        query_processed=True,
        products_found=len(products),
        suggestions_count=len(chat_data["suggestions"])
    )
    
    response = ChatFullResponse(
        chat_response=chat_response,
        metadata=metadata,
        status="success"
    )
    
    print(f"🚀 Returning chat response with {len(products)} products and {len(chat_data['suggestions'])} suggestions")
    return response

# ----------------------------------------------------------------
# Telegram-specific Formatter
# ----------------------------------------------------------------

def format_telegram_response(intent: str, keywords: str, products: list) -> str:
    """
    Formats a response string specifically for Telegram, using Markdown.
    """
    if intent == "greeting":
        return "¡Hola! 👋 Soy tu asistente de ferretería. ¿Qué necesitas buscar hoy?"

    elif intent == "help":
        return "Puedes preguntarme por cualquier producto. Por ejemplo: 'busco un martillo' o 'pintura roja'."

    elif intent == "search":
        if products:
            response = f"✅ Encontré {len(products)} productos para *{keywords}*:\n\n"
            for p in products[:3]: # Limitar a los 3 primeros para no saturar
                response += f"*{p.get('name')}*\n"
                response += f"  - SKU: `{p.get('sku')}`\n"
                response += f"  - Stock: {p.get('stock', 0)} unidades\n\n"
            if len(products) > 3:
                response += "_Y más... Intenta ser más específico si no encuentras lo que buscas._"
            return response
        else:
            return f"❌ No encontré productos para *{keywords}*. Por favor, intenta con otro término."

    return "¿Disculpa? No te he entendido. Intenta preguntarme por un producto."

# ----------------------------------------------------------------
# Telegram Bot Endpoint
# ----------------------------------------------------------------

class TelegramRequest(BaseModel):
    message: str
    user_id: Union[str, int]

@router.post("/chat/telegram")
def chat_with_telegram_bot(request: TelegramRequest):
    """
    Enhanced Telegram bot endpoint using OpenAI for intelligent responses.
    Now provides natural conversation, smart product search, and contextual help.
    """
    try:
        log_with_context(
            logger,
            "info",
            "Processing Telegram message with AI",
            user_id=str(request.user_id),
            message_length=len(request.message)
        )
        
        # Get OpenAI service
        openai_service = get_openai_service()
        
        # Generate intelligent response
        ai_response = openai_service.generate_smart_response(
            user_message=request.message,
            user_id=str(request.user_id),
            conversation_history=[]  # TODO: Implement conversation history in Phase 2
        )
        
        # Format response for Telegram
        response_text = ai_response['response']
        
        # Add product information if products were found
        if ai_response.get('products'):
            products = ai_response['products']
            
            # Add a separator if there are products
            if len(products) > 0:
                response_text += "\n\n📦 **Productos encontrados:**\n"
                
                for i, product in enumerate(products[:3], 1):  # Show max 3 products
                    stock_emoji = "✅" if product.get('stock', 0) > 0 else "❌"
                    
                    response_text += f"\n**{i}. {product.get('name', 'N/A')}**\n"
                    response_text += f"• SKU: `{product.get('sku', 'N/A')}`\n"
                    response_text += f"• Stock: {product.get('stock', 0)} unidades {stock_emoji}\n"
                    response_text += f"• Categoría: {product.get('category', 'N/A')}\n"
                    
                    # Add truncated description
                    description = product.get('description', '')
                    if description:
                        truncated_desc = description[:100] + "..." if len(description) > 100 else description
                        response_text += f"• {truncated_desc}\n"
        
        # Add helpful suggestions based on intent
        intent = ai_response.get('intent', 'general_help')
        if intent == 'product_search' and not ai_response.get('products'):
            response_text += "\n\n💡 **Sugerencia:** Intenta ser más específico o usa sinónimos."
        elif intent == 'greeting':
            response_text += "\n\n🔍 Puedes preguntarme por productos, precios, disponibilidad o hacer consultas técnicas."
        elif intent == 'purchase_intent':
            response_text += "\n\n🛒 Para procesar tu compra, necesitaré algunos datos. ¿Continuamos?"
        
        log_with_context(
            logger,
            "info",
            "AI response generated successfully",
            user_id=str(request.user_id),
            intent=intent,
            products_found=len(ai_response.get('products', [])),
            confidence=ai_response.get('confidence', 0.0)
        )
        
        return {"response": response_text}
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Error in AI-powered Telegram chat",
            user_id=str(request.user_id),
            error=str(e)
        )
        
        # Fallback to friendly error message
        return {
            "response": "🤖 Disculpa, tuve un pequeño problema procesando tu mensaje. ¿Puedes intentarlo de nuevo?\n\nSi persiste el problema, escribe 'ayuda' para opciones disponibles."
        } 