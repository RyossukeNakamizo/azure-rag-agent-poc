#!/bin/bash
set -e

RESOURCE_GROUP="rg-rag-poc"
TEMPLATE_FILE="infra/main-ai-foundry.bicep"
PARAMETERS_FILE="infra/parameters/ai-foundry.bicepparam"
DEPLOYMENT_NAME="ai-foundry-$(date +%Y%m%d-%H%M%S)"

usage() {
    echo "Usage: $0 [--validate|--whatif|--deploy]"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

case "$1" in
    --validate)
        echo "=== Step 1: Validation ==="
        az deployment group validate \
            --resource-group "$RESOURCE_GROUP" \
            --template-file "$TEMPLATE_FILE" \
            --parameters "$PARAMETERS_FILE" \
            --verbose
        echo ""
        echo "Next: ./scripts/deploy-ai-foundry.sh --whatif"
        ;;
    
    --whatif)
        echo "=== Step 2: What-If Analysis ==="
        az deployment group what-if \
            --resource-group "$RESOURCE_GROUP" \
            --template-file "$TEMPLATE_FILE" \
            --parameters "$PARAMETERS_FILE" \
            --result-format FullResourcePayloads
        echo ""
        echo "Next: ./scripts/deploy-ai-foundry.sh --deploy"
        ;;
    
    --deploy)
        echo "=== Step 3: Deployment ==="
        read -p "本番デプロイを実行しますか？ (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "キャンセルしました"
            exit 0
        fi
        
        az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --template-file "$TEMPLATE_FILE" \
            --parameters "$PARAMETERS_FILE" \
            --name "$DEPLOYMENT_NAME" \
            --verbose
        
        echo ""
        echo "=== Deployment完了 ==="
        az deployment group show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$DEPLOYMENT_NAME" \
            --query properties.outputs
        
        echo ""
        echo "AI Foundry Studio: https://ai.azure.com"
        ;;
    
    *)
        usage
        ;;
esac
