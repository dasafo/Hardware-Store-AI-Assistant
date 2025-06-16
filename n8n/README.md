# n8n Workflows - Hardware Store AI Assistant

Este directorio contiene los workflows de n8n para automatizar procesos y comunicaciones del asistente de ferretería.

## 🚀 Configuración Inicial

### 1. Iniciar n8n
```bash
cd /path/to/project
make start-n8n
```

### 2. Acceder a n8n
- URL: http://localhost:5678
- Usuario: admin
- Contraseña: n8n-admin-password

## 📋 Workflows Disponibles

### 1. Hardware Search Webhook (`hardware-search-webhook.json`)
**Propósito**: Procesa búsquedas de productos via webhook

**Endpoint**: `POST http://localhost:5678/webhook/search`

**Payload**:
```json
{
  "query": "martillo",
  "limit": 5
}
```

**Respuesta**:
```json
[
  {
    "sku": "SKU00001",
    "name": "Martillo de carpintero",
    "price": 25.99,
    "stock_quantity": 15
  }
]
```

### 2. Product Recommendations (`product-recommendations.json`)
**Propósito**: Obtiene recomendaciones de productos similares

**Endpoint**: `POST http://localhost:5678/webhook/recommend`

**Payload**:
```json
{
  "sku": "SKU00001"
}
```

### 3. WhatsApp Notifications (`whatsapp-notifications.json`)
**Propósito**: Procesa mensajes de WhatsApp y responde con búsquedas

**Endpoint**: `POST http://localhost:5678/webhook/whatsapp`

**Payload** (formato WhatsApp Business API):
```json
{
  "from": "5215551234567",
  "message": {
    "text": "busco un martillo"
  }
}
```

### 4. Inventory Alerts (`inventory-alerts.json`)
**Propósito**: Revisa inventario cada 6 horas y envía alertas

**Características**:
- Ejecuta automáticamente cada 6 horas
- Detecta productos agotados (stock = 0)
- Detecta productos con stock bajo (stock ≤ 10)
- Envía notificaciones al backend

## 🔧 Configuración de Variables

Copia el archivo `.env.example` a `.env` y configura las variables:

```bash
cp .env.example .env
```

Variables importantes:
- `N8N_BASIC_AUTH_USER`: Usuario para acceder a n8n
- `N8N_BASIC_AUTH_PASSWORD`: Contraseña para n8n
- `BACKEND_API_URL`: URL del backend (http://backend:8000)
- `BACKEND_API_KEY`: Clave API del backend

## 📡 Webhooks Disponibles

Todos los webhooks están disponibles en: `http://localhost:5678/webhook/{nombre}`

1. `/webhook/search` - Búsqueda de productos
2. `/webhook/recommend` - Recomendaciones
3. `/webhook/whatsapp` - Mensajes de WhatsApp
4. (Automático) - Alertas de inventario

## 🔗 Integración con Backend

Los workflows se comunican con el backend usando estos endpoints:

- `GET /products` - Lista todos los productos
- `POST /search` - Búsqueda semántica
- `GET /products/{sku}/similar` - Productos similares
- `POST /api/notifications/inventory` - Envío de alertas

## 📱 Integraciones Futuras

### WhatsApp Business API
Para conectar con WhatsApp real:
1. Configurar WhatsApp Business API
2. Actualizar `WHATSAPP_TOKEN` en `.env`
3. Configurar webhook de WhatsApp hacia n8n

### Telegram Bot
Para integrar Telegram:
1. Crear bot con BotFather
2. Configurar `TELEGRAM_BOT_TOKEN`
3. Crear workflow similar al de WhatsApp

## 🚨 Monitoreo y Alertas

El workflow de inventario envía alertas cuando:
- Un producto se agota completamente
- Un producto tiene menos de 10 unidades en stock
- Se ejecuta cada 6 horas automáticamente

## 🛠️ Comandos Útiles

```bash
# Iniciar solo n8n
docker-compose up n8n -d

# Ver logs de n8n
docker logs hsai-n8n -f

# Reiniciar n8n
docker-compose restart n8n

# Parar n8n
docker-compose stop n8n
```

## 📊 Métricas y Logs

n8n proporciona métricas automáticamente:
- Execuciones de workflows
- Errores y fallos
- Tiempo de respuesta
- Estado de webhooks

Accede a las métricas en: http://localhost:5678/workflows

## 🔐 Seguridad

- n8n está protegido con autenticación básica
- Los webhooks están disponibles públicamente (configura firewall si es necesario)
- Las comunicaciones con el backend usan API key
- Los datos se almacenan en volúmenes Docker persistentes