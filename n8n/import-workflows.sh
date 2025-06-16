#!/bin/bash

# Script para importar workflows a n8n
# Requiere que n8n esté ejecutándose

N8N_URL="http://localhost:5678"
WORKFLOWS_DIR="./workflows"

echo "🚀 Importando workflows a n8n..."

# Verificar que n8n esté ejecutándose
if ! curl -s $N8N_URL > /dev/null; then
    echo "❌ Error: n8n no está accesible en $N8N_URL"
    echo "Ejecuta 'make start-n8n' primero"
    exit 1
fi

echo "✅ n8n está accesible"

# Lista de workflows para importar
workflows=(
    "hardware-search-webhook.json"
    "product-recommendations.json"
    "whatsapp-notifications.json"
    "inventory-alerts.json"
)

# Función para importar un workflow
import_workflow() {
    local workflow_file=$1
    local workflow_path="$WORKFLOWS_DIR/$workflow_file"
    
    if [ ! -f "$workflow_path" ]; then
        echo "⚠️  Archivo no encontrado: $workflow_path"
        return 1
    fi
    
    echo "📤 Importando: $workflow_file"
    
    # Enviar workflow a n8n via API
    response=$(curl -s -X POST "$N8N_URL/api/v1/workflows" \
        -H "Content-Type: application/json" \
        -u "admin:n8n-admin-password" \
        -d @"$workflow_path")
    
    if echo "$response" | grep -q '"id"'; then
        echo "✅ Importado exitosamente: $workflow_file"
    else
        echo "❌ Error importando $workflow_file:"
        echo "$response"
    fi
}

# Importar todos los workflows
for workflow in "${workflows[@]}"; do
    import_workflow "$workflow"
    sleep 1
done

echo ""
echo "🎉 Proceso completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Accede a n8n: http://localhost:5678"
echo "2. Usuario: admin"
echo "3. Contraseña: n8n-admin-password"
echo "4. Activa los workflows importados"
echo "5. Prueba los webhooks disponibles"
echo ""
echo "🔗 Webhooks disponibles:"
echo "• POST http://localhost:5678/webhook/search"
echo "• POST http://localhost:5678/webhook/recommend"
echo "• POST http://localhost:5678/webhook/whatsapp"
echo ""