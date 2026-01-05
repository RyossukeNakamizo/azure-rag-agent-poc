#!/bin/bash
# =============================================================================
# RBAC Assignment Script for RAG POC
# =============================================================================
# Usage: 
#   ./scripts/assign-rbac.sh <user-email-or-object-id>
#   ./scripts/assign-rbac.sh --self  # 自分自身に権限付与
#
# Examples:
#   ./scripts/assign-rbac.sh user@example.com
#   ./scripts/assign-rbac.sh 12345678-1234-1234-1234-123456789012
#   ./scripts/assign-rbac.sh --self
# =============================================================================

set -euo pipefail

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-rag-poc}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
ENABLE_COSMOS_DB="${ENABLE_COSMOS_DB:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
show_usage() {
    echo "Usage: $0 <user-email-or-object-id>"
    echo ""
    echo "Options:"
    echo "  --self              Assign RBAC to currently signed-in user"
    echo "  --help              Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  RESOURCE_GROUP      Target resource group (default: rg-rag-poc)"
    echo "  ENVIRONMENT         Environment: dev|stg|prod (default: dev)"
    echo "  ENABLE_COSMOS_DB    Enable Cosmos DB RBAC: true|false (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0 user@example.com"
    echo "  $0 12345678-1234-1234-1234-123456789012"
    echo "  $0 --self"
    echo "  RESOURCE_GROUP=rg-rag-prod $0 user@example.com"
}

# Get user Object ID from email or return as-is if already an Object ID
get_object_id() {
    local input="$1"
    
    # Check if input looks like an Object ID (UUID format)
    if [[ "$input" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
        echo "$input"
        return 0
    fi
    
    # Otherwise, treat as email and look up
    print_info "Looking up Object ID for: $input"
    local object_id
    object_id=$(az ad user show --id "$input" --query id -o tsv 2>/dev/null) || {
        print_error "Failed to find user: $input"
        return 1
    }
    
    echo "$object_id"
}

# Get signed-in user's Object ID
get_self_object_id() {
    print_info "Getting Object ID for currently signed-in user..."
    az ad signed-in-user show --query id -o tsv
}

# Main RBAC assignment function
assign_rbac() {
    local object_id="$1"
    
    print_info "Starting RBAC assignment..."
    print_info "  Resource Group: $RESOURCE_GROUP"
    print_info "  Environment: $ENVIRONMENT"
    print_info "  Principal ID: $object_id"
    print_info "  Cosmos DB RBAC: $ENABLE_COSMOS_DB"
    echo ""
    
    # Verify resource group exists
    if ! az group show --name "$RESOURCE_GROUP" &>/dev/null; then
        print_error "Resource group '$RESOURCE_GROUP' not found"
        exit 1
    fi
    
    # Run what-if first
    print_info "Running what-if analysis..."
    az deployment group what-if \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/assign-rbac.bicep \
        --parameters userPrincipalId="$object_id" \
        --parameters environment="$ENVIRONMENT" \
        --parameters enableCosmosDbRbac="$ENABLE_COSMOS_DB"
    
    echo ""
    read -p "Proceed with deployment? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    # Deploy RBAC assignments
    print_info "Deploying RBAC assignments..."
    local deployment_name="rbac-assignment-$(date +%Y%m%d-%H%M%S)"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/assign-rbac.bicep \
        --parameters userPrincipalId="$object_id" \
        --parameters environment="$ENVIRONMENT" \
        --parameters enableCosmosDbRbac="$ENABLE_COSMOS_DB" \
        --name "$deployment_name" \
        --output table
    
    echo ""
    print_success "RBAC assignments completed successfully!"
    print_info "Deployment name: $deployment_name"
    
    # Show assigned roles
    echo ""
    print_info "Assigned roles:"
    az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --query "properties.outputs.assignedRoles.value" \
        --output table
}

# =============================================================================
# Main
# =============================================================================

# Check arguments
if [[ $# -lt 1 ]]; then
    show_usage
    exit 1
fi

case "$1" in
    --help|-h)
        show_usage
        exit 0
        ;;
    --self)
        OBJECT_ID=$(get_self_object_id)
        ;;
    *)
        OBJECT_ID=$(get_object_id "$1")
        ;;
esac

if [[ -z "$OBJECT_ID" ]]; then
    print_error "Failed to determine Object ID"
    exit 1
fi

print_success "Resolved Object ID: $OBJECT_ID"
echo ""

assign_rbac "$OBJECT_ID"
