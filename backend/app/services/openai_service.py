#!/usr/bin/env python3

import openai
import os
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import logger, log_with_context
from app.services.postgres import get_products_by_skus
from app.services.qdrant import search_in_qdrant
from app.services.embeddings import get_embedding

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI service with API key from environment"""
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini-2024-07-18')
        
        log_with_context(
            logger,
            "info",
            "OpenAI service initialized",
            model=self.model
        )
    
    def generate_smart_response(
        self, 
        user_message: str, 
        user_id: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate an intelligent response for hardware store customers
        
        Args:
            user_message: The user's message
            user_id: Unique identifier for the user
            conversation_history: Previous messages in the conversation
            
        Returns:
            Dict containing response text, intent, products found, and actions
        """
        try:
            # Analyze the message intent first
            intent_analysis = self._analyze_intent(user_message)
            
            # Get relevant products if it's a search intent
            products = []
            if intent_analysis.get('intent') == 'product_search':
                products = self._search_products(intent_analysis.get('search_query', user_message))
            
            # Generate contextual response
            response_text = self._generate_contextual_response(
                user_message=user_message,
                intent_analysis=intent_analysis,
                products=products,
                conversation_history=conversation_history or []
            )
            
            log_with_context(
                logger,
                "info",
                "Smart response generated",
                user_id=user_id,
                intent=intent_analysis.get('intent'),
                products_found=len(products)
            )
            
            return {
                'response': response_text,
                'intent': intent_analysis.get('intent'),
                'products': products,
                'confidence': intent_analysis.get('confidence', 0.8),
                'needs_followup': intent_analysis.get('needs_followup', False)
            }
            
        except Exception as e:
            log_with_context(
                logger,
                "error",
                "Error generating smart response",
                user_id=user_id,
                error=str(e)
            )
            
            # Fallback response
            return {
                'response': "Disculpa, tuve un problema procesando tu mensaje. ¿Puedes intentarlo de nuevo?",
                'intent': 'error',
                'products': [],
                'confidence': 0.0,
                'needs_followup': True
            }
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using OpenAI"""
        
        system_prompt = """Eres un experto analizador de intenciones para una ferretería.
        
Analiza el mensaje del cliente y clasifica la intención en una de estas categorías:
- greeting: saludos, presentaciones
- product_search: buscar productos específicos
- technical_question: preguntas técnicas sobre productos
- purchase_intent: quiere comprar algo
- stock_check: pregunta por disponibilidad
- price_inquiry: pregunta por precios
- complaint: quejas o problemas
- general_help: ayuda general o navegación

RESPONDE ÚNICAMENTE con un JSON válido con esta estructura:
{
  "intent": "categoria",
  "confidence": 0.95,
  "search_query": "términos de búsqueda si aplica",
  "needs_followup": true/false,
  "extracted_info": {
    "product_mentioned": "producto si se menciona",
    "quantity": "cantidad si se menciona",
    "urgency": "alta/media/baja"
  }
}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                "intent": "general_help",
                "confidence": 0.5,
                "needs_followup": True
            }
    
    def _search_products(self, search_query: str, limit: int = 5) -> List[Dict]:
        """Search for products using the existing vector search"""
        try:
            # Get embedding for the search query
            query_embedding = get_embedding(search_query)
            
            # Search in Qdrant - this returns a list of SKUs
            skus = search_in_qdrant(query_embedding, top_k=limit)
            
            if not skus:
                return []
            
            # Get detailed product information
            products = get_products_by_skus(skus)
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def _generate_contextual_response(
        self,
        user_message: str,
        intent_analysis: Dict,
        products: List[Dict],
        conversation_history: List[Dict]
    ) -> str:
        """Generate a contextual response based on intent and products found"""
        
        intent = intent_analysis.get('intent', 'general_help')
        
        # Build context for the LLM
        context_info = self._build_context_info(products, conversation_history)
        
        system_prompt = f"""Eres un asistente inteligente de una ferretería llamada "Ferretería El Martillo".

PERSONALIDAD:
- Amigable, profesional y conocedor
- Usa emojis de manera moderada
- Responde en español
- Sé conciso pero informativo

PRODUCTOS DISPONIBLES:
{context_info}

CONTEXTO DE CONVERSACIÓN:
{self._format_conversation_history(conversation_history)}

INSTRUCCIONES SEGÚN INTENCIÓN ({intent}):

Si es SALUDO:
- Saluda cordialmente y pregunta cómo puedes ayudar

Si es BÚSQUEDA DE PRODUCTO:
- Muestra los productos encontrados con formato claro
- Incluye nombre, precio, stock disponible
- Ofrece información adicional si es necesario

Si es PREGUNTA TÉCNICA:
- Responde basándote en las especificaciones del producto
- Si no tienes la info, ofrece contactar a un especialista

Si es INTENCIÓN DE COMPRA:
- Confirma el producto y cantidad
- Informa precio total
- Pregunta datos para procesar la compra

Si es CONSULTA DE STOCK:
- Informa disponibilidad clara
- Si hay poco stock, menciona urgencia

FORMATO DE RESPUESTA:
- Usa Markdown para Telegram
- **Negrita** para información importante
- • Viñetas para listas
- No uses caracteres especiales que rompan MarkdownV2

Responde de manera natural y útil."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "Disculpa, tuve un problema generando la respuesta. ¿Puedes ser más específico?"
    
    def _build_context_info(self, products: List[Dict], conversation_history: List[Dict]) -> str:
        """Build context information for the LLM"""
        if not products:
            return "No se encontraron productos relevantes."
        
        context = "PRODUCTOS ENCONTRADOS:\n"
        for product in products[:5]:  # Limit to top 5
            stock_status = "✅ Disponible" if product.get('stock', 0) > 0 else "❌ Sin stock"
            context += f"""
• **{product.get('name', 'N/A')}**
  - SKU: {product.get('sku', 'N/A')}
  - Categoría: {product.get('category', 'N/A')}
  - Stock: {product.get('stock', 0)} unidades ({stock_status})
  - Descripción: {product.get('description', 'N/A')[:100]}...
"""
        
        return context
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for context"""
        if not history:
            return "Primera interacción con el cliente."
        
        formatted = "HISTORIAL RECIENTE:\n"
        for msg in history[-3:]:  # Last 3 messages
            role = "Cliente" if msg.get('role') == 'user' else "Asistente"
            formatted += f"{role}: {msg.get('content', '')[:100]}...\n"
        
        return formatted

# Global service instance
_openai_service = None

def get_openai_service() -> OpenAIService:
    """Get or create the global OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service 