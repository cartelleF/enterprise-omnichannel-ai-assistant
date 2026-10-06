#!/bin/bash

set -e

STORAGE_ACCOUNT="stenterpriseaidev01"

echo "=========================================="
echo "Uploading SAP data"
echo "=========================================="

az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --destination "raw" \
  --source "data/raw/sap" \
  --destination-path "sap" \
  --auth-mode login \
  --overwrite

echo ""
echo "=========================================="
echo "Uploading CRM data"
echo "=========================================="

az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --destination "raw" \
  --source "data/raw/crm" \
  --destination-path "crm" \
  --auth-mode login \
  --overwrite

echo ""
echo "=========================================="
echo "Uploading documents"
echo "=========================================="

az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --destination "documents" \
  --source "data/raw/documents" \
  --auth-mode login \
  --overwrite

echo ""
echo "=========================================="
echo "Upload completed successfully"
echo "=========================================="
