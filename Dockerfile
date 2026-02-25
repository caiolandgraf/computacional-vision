FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Dependências do sistema (OpenCV + build)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Diretório da app
WORKDIR /app

# Copia dependências primeiro (cache)
COPY requirements.txt .

# Instala deps Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o resto do projeto
COPY . .

# Porta
EXPOSE 8000

# Start da aplicação
CMD ["python", "web/start.py", "--host", "0.0.0.0", "--port", "8000"]
