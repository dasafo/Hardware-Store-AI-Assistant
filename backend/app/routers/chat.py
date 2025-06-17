# routers/chat.py

from fastapi import APIRouter
from app.models.product import ChatRequest, ChatFullResponse, ChatResponse, ChatMetadata, ChatSuggestion, Product
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_skus
from datetime import datetime
import re

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