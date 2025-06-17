#!/usr/bin/env python3
"""
Script de prueba para el sistema de seguridad del Hardware Store AI Assistant.
Verifica que la autenticación por API key y el rate limiting funcionen correctamente.
"""

import requests
import time
import json
import os
from typing import Dict, Any

# Configuración de prueba
BASE_URL = "http://localhost:8000/api"
ADMIN_KEY = "admin-key-123"  # De .env.example
USER_KEY = "user-key-789"    # De .env.example
INVALID_KEY = "invalid-key"

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Imprime el resultado de una prueba de forma formateada"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    print()

def test_endpoint(endpoint: str, headers: Dict[str, str] = None, method: str = "GET") -> Dict[str, Any]:
    """Hace una petición a un endpoint y retorna la respuesta"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers)
        else:
            raise ValueError(f"Método HTTP no soportado: {method}")
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": True
        }
    except Exception as e:
        return {
            "status_code": None,
            "headers": {},
            "content": str(e),
            "success": False
        }

def test_security_headers():
    """Prueba que las cabeceras de seguridad se apliquen correctamente"""
    print("🔒 Probando cabeceras de seguridad...")
    
    response = test_endpoint("/security/headers/test")
    
    if not response["success"]:
        print_test_result("Headers Test - Request", False, f"Error: {response['content']}")
        return
    
    # Verificar cabeceras de seguridad
    headers = response["headers"]
    expected_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Content-Security-Policy",
        "Permissions-Policy",
        "X-Security-Middleware"
    ]
    
    missing_headers = [h for h in expected_headers if h not in headers]
    
    if missing_headers:
        print_test_result("Security Headers", False, f"Faltan cabeceras: {missing_headers}")
    else:
        print_test_result("Security Headers", True, "Todas las cabeceras de seguridad están presentes")

def test_api_key_authentication():
    """Prueba la autenticación por API key"""
    print("🔑 Probando autenticación por API key...")
    
    # Test 1: Endpoint público (no requiere API key)
    response = test_endpoint("/security/info")
    success = response["success"] and response["status_code"] == 200
    print_test_result("Public Endpoint Access", success, f"Status: {response['status_code']}")
    
    # Test 2: Endpoint que requiere API key válida - sin key
    response = test_endpoint("/security/api-key/validate", method="POST")
    success = response["status_code"] == 401
    print_test_result("Protected Endpoint - No Key", success, f"Status: {response['status_code']}")
    
    # Test 3: Endpoint que requiere API key válida - key inválida
    headers = {"X-API-Key": INVALID_KEY}
    response = test_endpoint("/security/api-key/validate", headers=headers, method="POST")
    success = response["status_code"] == 403
    print_test_result("Protected Endpoint - Invalid Key", success, f"Status: {response['status_code']}")
    
    # Test 4: Endpoint que requiere API key válida - user key
    headers = {"X-API-Key": USER_KEY}
    response = test_endpoint("/security/api-key/validate", headers=headers, method="POST")
    success = response["success"] and response["status_code"] == 200
    if success:
        key_type = response["content"].get("key_type")
        success = key_type == "user"
        print_test_result("User Key Validation", success, f"Key type: {key_type}")
    else:
        print_test_result("User Key Validation", False, f"Status: {response['status_code']}")
    
    # Test 5: Endpoint que requiere API key válida - admin key
    headers = {"X-API-Key": ADMIN_KEY}
    response = test_endpoint("/security/api-key/validate", headers=headers, method="POST")
    success = response["success"] and response["status_code"] == 200
    if success:
        key_type = response["content"].get("key_type")
        success = key_type == "admin"
        print_test_result("Admin Key Validation", success, f"Key type: {key_type}")
    else:
        print_test_result("Admin Key Validation", False, f"Status: {response['status_code']}")

def test_admin_only_endpoints():
    """Prueba endpoints que requieren permisos de administrador"""
    print("👑 Probando endpoints de administrador...")
    
    # Test 1: Endpoint admin - sin key
    response = test_endpoint("/security/rate-limit/stats")
    success = response["status_code"] == 401
    print_test_result("Admin Endpoint - No Key", success, f"Status: {response['status_code']}")
    
    # Test 2: Endpoint admin - user key (insuficiente)
    headers = {"X-API-Key": USER_KEY}
    response = test_endpoint("/security/rate-limit/stats", headers=headers)
    success = response["status_code"] == 403
    print_test_result("Admin Endpoint - User Key", success, f"Status: {response['status_code']}")
    
    # Test 3: Endpoint admin - admin key (correcto)
    headers = {"X-API-Key": ADMIN_KEY}
    response = test_endpoint("/security/rate-limit/stats", headers=headers)
    success = response["success"] and response["status_code"] == 200
    print_test_result("Admin Endpoint - Admin Key", success, f"Status: {response['status_code']}")

def test_rate_limiting():
    """Prueba el sistema de rate limiting"""
    print("⏱️  Probando rate limiting...")
    
    # Primero, reseteamos los rate limits (requiere admin key)
    headers = {"X-API-Key": ADMIN_KEY}
    reset_response = test_endpoint("/security/rate-limit/reset", headers=headers, method="POST")
    if not reset_response["success"]:
        print_test_result("Rate Limit Reset", False, "No se pudo resetear rate limits")
        return
    
    print_test_result("Rate Limit Reset", True, "Rate limits reseteados")
    
    # Test rate limiting para endpoint público
    print("   Probando rate limiting público (límite: 60/min)...")
    
    # Hacer varias peticiones rápidas
    success_count = 0
    rate_limited_count = 0
    
    for i in range(65):  # Más que el límite de 60
        response = test_endpoint("/security/rate-limit/check")
        if response["status_code"] == 200:
            success_count += 1
        elif response["status_code"] == 429:  # Too Many Requests
            rate_limited_count += 1
        
        # No hacer delay para probar el rate limiting
        if i % 20 == 0:
            print(f"   Petición {i+1}: Success={success_count}, Rate Limited={rate_limited_count}")
    
    # Deberíamos tener algunas peticiones exitosas y algunas rate limited
    rate_limiting_works = rate_limited_count > 0
    print_test_result("Rate Limiting", rate_limiting_works, 
                     f"Exitosas: {success_count}, Rate Limited: {rate_limited_count}")

def test_security_audit():
    """Prueba el endpoint de auditoría de seguridad"""
    print("🔍 Probando auditoría de seguridad...")
    
    headers = {"X-API-Key": ADMIN_KEY}
    response = test_endpoint("/security/audit", headers=headers)
    
    success = response["success"] and response["status_code"] == 200
    if success:
        audit_data = response["content"]
        features = audit_data.get("security_features", {})
        recommendations = audit_data.get("recommendations", [])
        
        details = f"Features: {len(features)}, Recommendations: {len(recommendations)}"
        print_test_result("Security Audit", True, details)
        
        # Mostrar algunas estadísticas
        if "rate_limiting" in features:
            rl_info = features["rate_limiting"]
            print(f"   Rate Limiting - Active IPs: {rl_info.get('active_ips', 'N/A')}")
        
        if "api_key_auth" in features:
            auth_info = features["api_key_auth"]
            print(f"   API Keys - Admin: {auth_info.get('admin_keys', 'N/A')}, User: {auth_info.get('user_keys', 'N/A')}")
    else:
        print_test_result("Security Audit", False, f"Status: {response['status_code']}")

def main():
    """Ejecuta todas las pruebas de seguridad"""
    print("🚀 Iniciando pruebas de seguridad del Hardware Store AI Assistant")
    print("=" * 70)
    print()
    
    # Verificar que el servidor esté ejecutándose
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está respondiendo correctamente")
            print(f"   URL: {BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            return
    except Exception as e:
        print("❌ No se puede conectar al servidor")
        print(f"   URL: {BASE_URL}")
        print(f"   Error: {e}")
        print("\n💡 Asegúrate de que el servidor esté ejecutándose en localhost:8000")
        return
    
    print("✅ Servidor conectado correctamente")
    print()
    
    # Ejecutar todas las pruebas
    test_security_headers()
    test_api_key_authentication()
    test_admin_only_endpoints()
    test_rate_limiting()
    test_security_audit()
    
    print("=" * 70)
    print("🏁 Pruebas de seguridad completadas")
    print()
    print("📝 Notas:")
    print("   - Si alguna prueba falla, revisa los logs del servidor")
    print("   - Las API keys de prueba están definidas en .env.example")
    print("   - El rate limiting puede tardar un minuto en resetearse")

if __name__ == "__main__":
    main() 