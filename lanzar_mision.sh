#!/bin/bash

echo "🛠️ Iniciando misión galáctica..."

# Paso 1: Ejecutar el productor
echo "🚀 Lanzando el producer..."
docker compose run --rm producer python main.py

# Paso 2: Esperar unos segundos para asegurar commits en DB
echo "🕒 Esperando sincronización interestelar (2s)..."
sleep 2

# Paso 3: Lanzar el agente
echo "🛰️ Desplegando el agent..."
docker compose run --rm agent python main.py