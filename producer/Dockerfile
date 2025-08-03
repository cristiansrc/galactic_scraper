# Imagen base liviana con Python
FROM python:3.11-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Comando de arranque
CMD ["python", "main.py"]