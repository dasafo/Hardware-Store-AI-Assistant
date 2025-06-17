# 🏪 Hardware Store AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

An enterprise-grade AI-powered assistant designed specifically for hardware stores. This system combines intelligent search capabilities with natural language chat functionality to enhance customer experience and streamline operations.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Security](#-security)
- [n8n Workflows](#-n8n-workflows)
- [Demo & Testing](#-demo--testing)
- [Development](#-development)
- [Monitoring](#-monitoring)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔍 Intelligent Search
- **Vector-based semantic search** using Qdrant for finding products by meaning, not just keywords
- **Natural language queries** - "I need something to fix a leaky pipe" → relevant plumbing products
- **Hybrid search** combining traditional text search with AI-powered semantic matching
- **Real-time product recommendations** based on user queries and context
- **Cached results** for improved performance and reduced latency

### 🤖 AI Chat Assistant
- **Context-aware conversations** powered by OpenAI GPT-4
- **Product recommendations** with detailed specifications and pricing
- **Technical support** for hardware projects and troubleshooting
- **Multi-turn conversations** that remember context throughout the session
- **Integration-ready** chat API for embedding in websites, apps, or messaging platforms

### 🔗 Integration Readiness
- **n8n workflow automation** for WhatsApp commerce and customer service
- **RESTful API** with comprehensive documentation and examples
- **Webhook support** for real-time notifications and integrations
- **Third-party integrations** ready for POS systems, inventory management, and CRM
- **Multi-channel support** for web, mobile, and messaging platforms

### 🔐 Enterprise Security
- **API key authentication** with role-based access control
- **Rate limiting** to prevent abuse and ensure fair usage
- **Security headers** and OWASP compliance
- **Comprehensive logging** for audit trails and monitoring
- **Environment-based configuration** for secure deployment

### 📊 Performance & Monitoring
- **Health checks** for all system components (API, Database, Cache, Vector Store)
- **Performance metrics** with response time tracking and system monitoring
- **Caching system** using Redis for frequently accessed data
- **Database optimization** with connection pooling and query optimization
- **Real-time system status** dashboard and monitoring endpoints

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Interface]
        API_CLIENT[API Clients]
        N8N[n8n Workflows]
        WHATSAPP[WhatsApp Integration]
    end
    
    subgraph "API Layer"
        FASTAPI[FastAPI Backend]
        AUTH[Authentication]
        RATE[Rate Limiting]
    end
    
    subgraph "Business Logic"
        SEARCH[Search Service]
        CHAT[Chat Service]
        RECOMMEND[Recommendation Engine]
        CACHE_SVC[Cache Service]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        QDRANT[(Qdrant Vector DB)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI GPT-4]
        MONITORING[Health Monitoring]
    end
    
    WEB --> FASTAPI
    API_CLIENT --> FASTAPI
    N8N --> FASTAPI
    WHATSAPP --> N8N
    
    FASTAPI --> AUTH
    FASTAPI --> RATE
    FASTAPI --> SEARCH
    FASTAPI --> CHAT
    FASTAPI --> RECOMMEND
    
    SEARCH --> QDRANT
    SEARCH --> POSTGRES
    CHAT --> OPENAI
    RECOMMEND --> QDRANT
    CACHE_SVC --> REDIS
    
    SEARCH --> CACHE_SVC
    CHAT --> CACHE_SVC
    RECOMMEND --> CACHE_SVC
    
    FASTAPI --> MONITORING
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.11 | High-performance async API framework |
| **Database** | PostgreSQL 15 | Primary data storage for products and transactions |
| **Vector Search** | Qdrant | Semantic search and product recommendations |
| **Cache** | Redis 7 | Session management and performance optimization |
| **AI/ML** | OpenAI GPT-4 | Natural language processing and chat functionality |
| **Workflow** | n8n | Automation and integration workflows |
| **Containerization** | Docker + Docker Compose | Consistent deployment and scaling |
| **Documentation** | FastAPI Swagger/OpenAPI | Interactive API documentation |
| **Monitoring** | Built-in health checks | System monitoring and alerting |

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development)
- **OpenAI API Key** (for AI chat functionality)
- **Minimum 4GB RAM** and **2GB free disk space**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/hardware-store-ai-assistant.git
   cd hardware-store-ai-assistant
   ```

2. **Run the quick setup script**
   ```bash
   ./scripts/quick-start.sh
   ```

   Or manually set up:

3. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OpenAI API key
   ```

4. **Start all services**
   ```bash
   make up
   ```

5. **Initialize vector database**
   ```bash
   make index-qdrant
   ```

### Verification

1. **Check system health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Access API documentation**
   ```
   http://localhost:8000/docs
   ```

3. **Run the interactive demo**
   ```bash
   python scripts/demo.py
   ```

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration (.env)
```env
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/hardware_store
POSTGRES_DB=hardware_store
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Qdrant Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Security
SECRET_KEY=your-secret-key-here
API_KEY_ADMIN=admin-api-key-here
API_KEY_USER=user-api-key-here

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

#### Security Settings
```env
# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
ALLOWED_METHODS=GET,POST,PUT,DELETE
ALLOWED_HEADERS=*

# Security Headers
SECURITY_HEADERS_ENABLED=true
HTTPS_REDIRECT=false  # Set to true in production
```

#### n8n Configuration
```env
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=password
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
```

### Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| **Backend API** | 8000 | Main FastAPI application |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Cache and session store |
| **Qdrant** | 6333 | Vector database for semantic search |
| **n8n** | 5678 | Workflow automation platform |
| **pgAdmin** | 5050 | Database administration interface |

## 📚 API Documentation

### Search Endpoints

#### POST `/search`
Search for products using natural language or keywords.

**Request:**
```json
{
  "query": "hammer for woodworking",
  "limit": 10,
  "filters": {
    "category": "tools",
    "price_range": [10, 100]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "sku": "HAMMER001",
      "name": "Professional Claw Hammer",
      "description": "16oz steel claw hammer with fiberglass handle",
      "price": 24.99,
      "category": "Hand Tools",
      "similarity_score": 0.95,
      "in_stock": true
    }
  ],
  "total": 1,
  "query_time": 0.045
}
```

#### GET `/search/suggestions`
Get search suggestions based on partial input.

**Parameters:**
- `q`: Partial query string
- `limit`: Number of suggestions (default: 5)

### Chat Endpoints

#### POST `/chat`
Start or continue a conversation with the AI assistant.

**Request:**
```json
{
  "message": "I need help choosing a drill for home projects",
  "session_id": "user-123-session",
  "context": {
    "previous_searches": ["drill", "power tools"],
    "user_type": "diy_enthusiast"
  }
}
```

**Response:**
```json
{
  "response": "I'd be happy to help you choose the right drill! For home projects, I recommend considering these factors...",
  "session_id": "user-123-session",
  "suggested_products": [
    {
      "sku": "DRILL001",
      "name": "Cordless Drill Kit",
      "reason": "Perfect for DIY projects with variable speed control"
    }
  ],
  "follow_up_questions": [
    "What types of materials will you be drilling?",
    "Do you prefer cordless or corded tools?"
  ]
}
```

#### GET `/chat/history/{session_id}`
Retrieve conversation history for a session.

### Product Endpoints

#### GET `/products/{sku}/details`
Get detailed information about a specific product.

**Response:**
```json
{
  "sku": "HAMMER001",
  "name": "Professional Claw Hammer",
  "description": "16oz steel claw hammer with ergonomic fiberglass handle",
  "price": 24.99,
  "category": "Hand Tools",
  "specifications": {
    "weight": "16oz",
    "handle_material": "Fiberglass",
    "head_material": "Steel"
  },
  "in_stock": true,
  "stock_quantity": 45,
  "related_products": ["HAMMER002", "NAILS001"]
}
```

#### POST `/products/{sku}/recommend`
Get product recommendations based on a specific product.

### Security Endpoints

#### POST `/security/api-key/validate`
Validate an API key and get associated permissions.

**Headers:**
```
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "valid": true,
  "key_type": "admin",
  "permissions": ["read", "write", "admin"],
  "rate_limit": {
    "requests_remaining": 95,
    "reset_time": "2024-01-01T12:00:00Z"
  }
}
```

#### GET `/security/rate-limit/stats`
Get current rate limiting statistics.

### Health & Monitoring Endpoints

#### GET `/health`
Overall system health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "cache": "healthy",
    "vector_db": "healthy"
  },
  "version": "1.0.0"
}
```

#### GET `/health/{service}`
Check specific service health:
- `/health/postgres` - Database connection
- `/health/redis` - Cache connection
- `/health/qdrant` - Vector database connection

#### GET `/metrics`
System performance metrics.

**Response:**
```json
{
  "requests_total": 1250,
  "requests_per_second": 12.5,
  "average_response_time": 0.045,
  "cache_hit_rate": 0.85,
  "active_sessions": 23,
  "database_connections": 5
}
```

## 🔐 Security

### Authentication
- **API Key Authentication**: All endpoints require valid API keys
- **Role-based Access**: Different permission levels (admin, user, readonly)
- **Session Management**: Secure session handling with Redis

### Authorization
```python
# Admin access required
@require_api_key(role="admin")
async def admin_endpoint():
    pass

# User access required
@require_api_key(role="user")
async def user_endpoint():
    pass
```

### Rate Limiting
- **Per-key rate limiting**: 100 requests per minute by default
- **Configurable limits**: Different limits for different API key types
- **Graceful degradation**: Informative error messages when limits exceeded

### Security Headers
- **CORS protection**: Configurable allowed origins
- **Security headers**: HSTS, CSP, X-Frame-Options
- **Request validation**: Input sanitization and validation

## 🔄 n8n Workflows

### Pre-built Workflows

#### WhatsApp Commerce Integration
- **Customer inquiries**: Automated responses to product questions
- **Order processing**: Handle orders through WhatsApp Business API
- **Inventory updates**: Real-time stock level notifications
- **Customer support**: Escalation to human agents when needed

#### Setup Instructions

1. **Access n8n interface**
   ```
   http://localhost:5678
   ```

2. **Import workflows**
   ```bash
   make import-workflows
   ```

3. **Configure WhatsApp Business API**
   - Add your WhatsApp Business credentials
   - Configure webhook endpoints
   - Test the integration

### Available Workflows
- `whatsapp-commerce.json` - Complete WhatsApp commerce integration
- `customer-support.json` - Automated customer support workflows
- `inventory-alerts.json` - Low stock and reorder notifications
- `analytics-reporting.json` - Daily/weekly performance reports

## 🧪 Demo & Testing

### Interactive Demo

Run the comprehensive demo script:
```bash
python scripts/demo.py
```

This will test:
- ✅ All API endpoints
- ✅ Search functionality
- ✅ Chat capabilities
- ✅ Security features
- ✅ Performance metrics
- ✅ System health

### Manual Testing

#### Search API
```bash
# Basic search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "cordless drill", "limit": 5}'

# Advanced search with filters
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "power tools",
    "limit": 10,
    "filters": {
      "category": "Power Tools",
      "price_range": [50, 200],
      "in_stock": true
    }
  }'
```

#### Chat API
```bash
# Start conversation
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "I need help choosing a saw for cutting lumber",
    "session_id": "test-session-123"
  }'
```

#### Health Checks
```bash
# Overall health
curl http://localhost:8000/health

# Specific services
curl http://localhost:8000/health/postgres
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/qdrant
```

## 💻 Development

### Local Setup

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd hardware-store-ai-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run in development mode**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Available Make Commands

```bash
# Docker Management
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make rebuild         # Rebuild and start services
make logs            # View logs from all services

# Database Management
make index-qdrant    # Initialize vector database with product embeddings
make db-migrate      # Run database migrations
make db-seed         # Seed database with sample data

# Development
make test            # Run all tests
make lint            # Run code linting
make format          # Format code with black
make type-check      # Run type checking with mypy

# n8n Workflows
make start-n8n       # Start n8n workflow service
make stop-n8n        # Stop n8n workflow service
make import-workflows # Import pre-built workflows

# Monitoring
make health-check    # Check all service health
make performance     # Run performance tests
```

### Project Structure

```
hardware-store-ai-assistant/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic services
│   │   ├── models/         # Data models and schemas
│   │   ├── utils/          # Utility functions
│   │   └── middleware/     # Custom middleware
│   ├── tests/              # Test files
│   ├── Dockerfile          # Backend container configuration
│   └── requirements.txt    # Python dependencies
├── scripts/                # Utility and demo scripts
│   ├── demo.py            # Interactive demo script
│   └── quick-start.sh     # Automated setup script
├── docs/                   # Documentation
│   ├── ROADMAP.md         # Project roadmap
│   └── api-examples/      # API usage examples
├── n8n/                    # n8n workflow configurations
│   └── workflows/         # Pre-built workflow templates
├── infra/                  # Infrastructure configuration
│   └── docker-compose.yml # Multi-service container setup
├── Makefile               # Development and deployment commands
└── README.md              # This file
```

## 📊 Monitoring

### Health Checks

The system provides comprehensive health monitoring:

- **API Health**: `/health` - Overall system status
- **Database Health**: `/health/postgres` - PostgreSQL connection and query performance
- **Cache Health**: `/health/redis` - Redis connection and memory usage
- **Vector DB Health**: `/health/qdrant` - Qdrant connection and collection status

### Performance Metrics

Monitor system performance through:

- **Response Times**: Average API response times
- **Cache Hit Rates**: Redis cache effectiveness
- **Database Performance**: Query execution times and connection pool status
- **Search Quality**: Semantic search accuracy and relevance scores

### Logging

All components provide structured logging:

```bash
# View real-time logs
make logs

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f qdrant
```

## 🗺️ Roadmap

### Version 2.0 - Intelligence & Analytics (Q2 2024)
- **Advanced Analytics Dashboard**: Customer behavior insights and sales analytics
- **Multi-language Support**: Spanish, French, and Portuguese language support
- **Enhanced AI Capabilities**: GPT-4 Turbo integration and custom fine-tuned models
- **Computer Vision**: Product image recognition and visual search capabilities
- **Predictive Analytics**: Demand forecasting and inventory optimization

### Version 2.1 - Mobile & Integrations (Q3 2024)
- **Mobile Applications**: Native iOS and Android apps
- **Advanced Integrations**: Shopify, WooCommerce, and major POS systems
- **Voice Interface**: Voice-activated search and ordering
- **Augmented Reality**: AR product visualization and placement tools

### Version 3.0 - Enterprise & Scale (Q4 2024)
- **Multi-tenant Architecture**: Support for multiple store chains
- **Advanced Security**: SSO, LDAP integration, and compliance certifications
- **AI-powered Automation**: Intelligent inventory management and pricing optimization
- **Enterprise Analytics**: Advanced reporting and business intelligence tools

### Version 4.0 - Innovation & Future (Q1 2025)
- **Immersive Technologies**: VR showroom experiences
- **IoT Integration**: Smart shelf monitoring and automated reordering
- **Blockchain Integration**: Supply chain transparency and authentication
- **Edge Computing**: Local AI processing for improved performance

For detailed roadmap information, see [docs/ROADMAP.md](docs/ROADMAP.md).

## 🤝 Contributing

We welcome contributions from the community! Please read our contributing guidelines:

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use type hints for all functions
- Write comprehensive tests for new features
- Update documentation for API changes

### Testing
```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏪 About

The Hardware Store AI Assistant is designed to revolutionize the hardware retail industry by providing intelligent, AI-powered customer experiences. Whether you're a small local hardware store or a large retail chain, this system helps you:

- **Improve Customer Experience**: Instant, accurate product recommendations and technical support
- **Increase Sales**: AI-powered upselling and cross-selling recommendations
- **Reduce Support Costs**: Automated customer service and technical support
- **Streamline Operations**: Integrated workflows and automation tools
- **Gain Insights**: Advanced analytics and customer behavior tracking

Built with modern technologies and enterprise-grade security, this system is ready to scale with your business needs.

## 👤 Author

**David Salas**
- Website: [dasafodata.com](https://dasafodata.com)
- GitHub: [@dasafo](https://github.com/dasafo)
- LinkedIn: [David Salas](https://www.linkedin.com/in/dasafodata/)

---

<p align="center">
  <sub>Created with ❤️ by David Salas - dasafodata</sub>
</p> 🚀