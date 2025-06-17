# 🔒 Sistema de Seguridad - Hardware Store AI Assistant

## Resumen

El Hardware Store AI Assistant implementa un sistema de seguridad robusto que incluye:

- **Autenticación por API Key** con roles (Admin/User)
- **Rate Limiting** por IP con límites diferenciados
- **Cabeceras de Seguridad** automáticas
- **Logging de Seguridad** estructurado
- **Endpoints de Monitoreo** y auditoría

## 🔑 Autenticación por API Key

### Configuración

Las API keys se configuran mediante variables de entorno:

```bash
# Claves de administrador (separadas por comas)
ADMIN_API_KEYS=admin-key-123,admin-key-456

# Claves de usuario (separadas por comas)  
USER_API_KEYS=user-key-789,user-key-abc
```

### Tipos de Claves

| Tipo | Permisos | Rate Limit | Uso |
|------|----------|------------|-----|
| **Admin** | Acceso completo | 300 req/min | Administración, métricas, auditoría |
| **User** | Endpoints protegidos | 120 req/min | Aplicaciones cliente |
| **Público** | Endpoints públicos | 60 req/min | Acceso sin autenticación |

### Uso en Requests

```bash
# Con clave de administrador
curl -H "X-API-Key: admin-key-123" http://localhost:8000/api/security/audit

# Con clave de usuario
curl -H "X-API-Key: user-key-789" http://localhost:8000/api/security/api-key/validate
```

## ⏱️ Rate Limiting

### Configuración

```bash
# Límites por minuto
RATE_LIMIT_DEFAULT=60    # IPs sin API key
RATE_LIMIT_USER=120      # Claves de usuario
RATE_LIMIT_ADMIN=300     # Claves de administrador
```

### Funcionamiento

- **Ventana deslizante** de 1 minuto
- **Seguimiento por IP** automático
- **Headers informativos** en cada respuesta:
  - `X-RateLimit-Limit`: Límite actual
  - `X-RateLimit-Remaining`: Requests restantes
  - `X-RateLimit-Reset`: Timestamp de reset

### Respuesta de Rate Limit

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

## 🛡️ Cabeceras de Seguridad

Se aplican automáticamente a todas las respuestas:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
Permissions-Policy: geolocation=(), microphone=(), camera=()
X-Security-Middleware: active
```

## 📊 Endpoints de Seguridad

### Públicos

#### `GET /api/security/info`
Información general del sistema de seguridad.

```json
{
  "rate_limiting_enabled": true,
  "api_key_auth_enabled": true,
  "admin_keys_count": 2,
  "user_keys_count": 2,
  "rate_limits": {
    "default": 60,
    "user": 120,
    "admin": 300
  },
  "security_headers_enabled": true
}
```

#### `GET /api/security/rate-limit/check`
Verifica el estado actual del rate limit.

```json
{
  "allowed": true,
  "limit": 60,
  "remaining": 45,
  "reset": 1703123456,
  "client_ip": "192.168.1.100"
}
```

#### `GET /api/security/headers/test`
Endpoint para verificar cabeceras de seguridad.

### Protegidos (Requieren API Key)

#### `POST /api/security/api-key/validate`
Valida y retorna información sobre la API key utilizada.

```json
{
  "valid": true,
  "key_type": "admin",
  "message": "Valid admin API key"
}
```

### Solo Administradores

#### `GET /api/security/rate-limit/stats`
Estadísticas detalladas del rate limiting.

```json
{
  "active_ips": 15,
  "total_requests_last_minute": 234,
  "tracked_ips": 45,
  "limits": {
    "default": 60,
    "user": 120,
    "admin": 300
  }
}
```

#### `POST /api/security/rate-limit/reset`
Resetea todos los contadores de rate limiting.

#### `GET /api/security/audit`
Auditoría completa del sistema de seguridad.

```json
{
  "timestamp": "2023-12-21T10:30:00Z",
  "security_features": {
    "rate_limiting": {
      "enabled": true,
      "status": "active",
      "active_ips": 15,
      "total_requests": 234
    },
    "api_key_auth": {
      "enabled": true,
      "admin_keys": 2,
      "user_keys": 2
    },
    "security_headers": {
      "enabled": true,
      "status": "active"
    },
    "logging": {
      "enabled": true,
      "structured": true
    }
  },
  "recommendations": [
    "Ensure API keys are rotated regularly",
    "Monitor rate limiting logs for abuse patterns",
    "Review security headers periodically"
  ]
}
```

## 🔧 Implementación Técnica

### Middleware

1. **SecurityMiddleware**: Aplica rate limiting y cabeceras de seguridad
2. **LoggingMiddleware**: Registra todas las peticiones con contexto de seguridad

### Dependencias FastAPI

```python
from app.utils.security import require_admin_key, require_api_key

@router.get("/admin-endpoint")
def admin_only(auth=Depends(require_admin_key)):
    # Solo accesible con clave de administrador
    pass

@router.get("/protected-endpoint")  
def protected(auth=Depends(require_api_key)):
    # Accesible con cualquier clave válida
    pass
```

### Compatibilidad Legacy

El sistema mantiene compatibilidad con el `admin_guard` existente:

```python
from app.utils.auth import admin_guard

@router.post("/legacy-endpoint")
def legacy(auth=Depends(admin_guard)):
    # Funciona con el sistema nuevo y legacy
    pass
```

## 📝 Logging de Seguridad

Todos los eventos de seguridad se registran con contexto completo:

```json
{
  "timestamp": "2023-12-21T10:30:00Z",
  "level": "WARNING",
  "message": "Rate limit exceeded",
  "client_ip": "192.168.1.100",
  "endpoint": "/api/search",
  "user_agent": "curl/7.68.0",
  "rate_limit": 60,
  "current_requests": 61
}
```

## 🧪 Pruebas

Ejecuta el script de pruebas incluido:

```bash
cd backend
python test_security.py
```

El script verifica:
- ✅ Cabeceras de seguridad
- ✅ Autenticación por API key
- ✅ Autorización de endpoints admin
- ✅ Rate limiting funcional
- ✅ Auditoría de seguridad

## 🚀 Despliegue en Producción

### Variables de Entorno Críticas

```bash
# CAMBIAR ESTOS VALORES EN PRODUCCIÓN
ADMIN_API_KEYS=your-secure-admin-key-1,your-secure-admin-key-2
USER_API_KEYS=your-secure-user-key-1,your-secure-user-key-2

# Ajustar según necesidades
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_USER=200  
RATE_LIMIT_ADMIN=500
```

### Recomendaciones

1. **Rotar API Keys** regularmente
2. **Monitorear logs** de seguridad
3. **Ajustar rate limits** según tráfico
4. **Configurar alertas** para eventos de seguridad
5. **Usar HTTPS** en producción
6. **Configurar CORS** específicamente

### Monitoreo

- Revisar `/api/security/audit` regularmente
- Monitorear `/api/security/rate-limit/stats` 
- Configurar alertas en logs de nivel WARNING/ERROR

## 🔍 Troubleshooting

### Rate Limit Alcanzado
```bash
# Verificar estado actual
curl http://localhost:8000/api/security/rate-limit/check

# Resetear (solo admin)
curl -X POST -H "X-API-Key: admin-key" http://localhost:8000/api/security/rate-limit/reset
```

### API Key Inválida
- Verificar variable de entorno
- Confirmar formato del header: `X-API-Key: your-key`
- Validar con: `/api/security/api-key/validate`

### Cabeceras de Seguridad
- Verificar con: `/api/security/headers/test`
- Revisar logs del SecurityMiddleware

## 📚 Referencias

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [HTTP Security Headers](https://owasp.org/www-project-secure-headers/) 