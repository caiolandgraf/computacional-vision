# 📦 Guia de Instalação Completo

Este guia fornece instruções detalhadas para instalação do Sistema de Detecção de Mato Alto em diferentes sistemas operacionais.

## 📋 Índice

- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Instalação por Sistema](#-instalação-por-sistema)
- [Instalação Manual](#-instalação-manual)
- [Verificação da Instalação](#-verificação-da-instalação)
- [Solução de Problemas](#-solução-de-problemas)
- [Configuração Avançada](#-configuração-avançada)

## 🔧 Pré-requisitos

### Requisitos Mínimos
- **Python**: 3.8 ou superior
- **RAM**: 4GB (recomendado: 8GB+)
- **Espaço em Disco**: 2GB livres
- **Sistema**: macOS 10.14+, Ubuntu 18.04+, Windows 10+

### Requisitos Recomendados
- **Python**: 3.11 ou 3.12
- **RAM**: 16GB
- **Espaço em Disco**: 5GB livres
- **GPU**: Opcional, para deep learning

## 🚀 Instalação Rápida

### Método Automatizado (Recomendado)

```bash
# 1. Clone o repositório
git clone <repository-url>
cd computacional-vision

# 2. Execute o script de instalação
chmod +x setup.sh
./setup.sh

# 3. Teste a instalação
source venv/bin/activate
python3 src/main.py --help
```

## 🖥️ Instalação por Sistema

### macOS

#### Opção 1: Homebrew (Recomendado)

```bash
# Instalar Homebrew (se necessário)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python
brew install python@3.11

# Instalar dependências do sistema (opcional)
brew install cmake pkg-config

# Clone e instale o projeto
git clone <repository-url>
cd computacional-vision
./setup.sh
```

#### Opção 2: Python.org

```bash
# 1. Baixe Python de https://www.python.org/downloads/
# 2. Instale seguindo as instruções
# 3. Verifique a instalação:
python3 --version

# 4. Continue com instalação do projeto
git clone <repository-url>
cd computacional-vision
./setup.sh
```

### Linux (Ubuntu/Debian)

```bash
# Atualizar repositórios
sudo apt update

# Instalar Python e dependências
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev
sudo apt install -y build-essential cmake pkg-config

# Instalar Git (se necessário)
sudo apt install -y git

# Clone e instale o projeto
git clone <repository-url>
cd computacional-vision
./setup.sh
```

### Linux (CentOS/RHEL/Fedora)

```bash
# Para CentOS/RHEL
sudo yum install -y python3 python3-pip python3-devel
sudo yum install -y mesa-libGL glib2 libSM libXext libXrender
sudo yum groupinstall -y "Development Tools"

# Para Fedora (usar dnf)
sudo dnf install -y python3 python3-pip python3-devel
sudo dnf install -y mesa-libGL glib2 libSM libXext libXrender
sudo dnf groupinstall -y "Development Tools"

# Continue com a instalação
git clone <repository-url>
cd computacional-vision
./setup.sh
```

### Windows

#### Opção 1: Python.org + Git

```powershell
# 1. Instale Python de https://www.python.org/downloads/
#    - Marque "Add Python to PATH"
#    - Marque "Install pip"

# 2. Instale Git de https://git-scm.com/downloads

# 3. Abra PowerShell ou Command Prompt
git clone <repository-url>
cd computacional-vision

# 4. Execute setup (adapte para Windows)
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Opção 2: WSL (Windows Subsystem for Linux)

```bash
# 1. Instale WSL2
# 2. Instale distribuição Ubuntu
# 3. Siga instruções para Linux Ubuntu acima
```

#### Opção 3: Anaconda

```bash
# 1. Instale Anaconda de https://www.anaconda.com/
# 2. Abra Anaconda Prompt

conda create -n grass-detector python=3.11
conda activate grass-detector

git clone <repository-url>
cd computacional-vision
pip install -r requirements.txt
```

## 🔨 Instalação Manual

Se o script automatizado não funcionar, siga estes passos:

### 1. Verificar Python

```bash
python3 --version
# Deve mostrar 3.8 ou superior
```

### 2. Criar Ambiente Virtual

```bash
python3 -m venv venv

# Ativar (Linux/macOS)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate
```

### 3. Atualizar pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Instalar Dependências

```bash
# Dependências essenciais primeiro
pip install opencv-python>=4.8.1
pip install numpy>=1.22.0
pip install scikit-learn>=1.3.0
pip install scipy>=1.8.0

# Todas as dependências
pip install -r requirements.txt
```

### 5. Criar Diretórios

```bash
mkdir -p output models logs
```

### 6. Testar Instalação

```bash
python3 -c "
import cv2, numpy, sklearn, scipy
print('✅ Dependências principais OK')
print(f'OpenCV: {cv2.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'SciPy: {scipy.__version__}')
"
```

## ✅ Verificação da Instalação

### Teste Básico

```bash
# Ativar ambiente
source venv/bin/activate

# Teste de importação
python3 -c "
import sys
sys.path.append('src')
from detector import GrassDetector
print('✅ Sistema importado com sucesso!')
"

# Teste de ajuda
python3 src/main.py --help
```

### Teste com Imagem

```bash
# Se houver imagens de exemplo
python3 src/main.py --image examples/exemplo_mato_alto.jpg --method color

# Verificar se arquivo foi criado em output/
ls -la output/
```

### Teste Completo

```bash
# Execute testes automatizados
python3 examples/demo.py
python3 examples/test_reliability.py
```

## 🐛 Solução de Problemas

### Problema: `ModuleNotFoundError: No module named 'cv2'`

```bash
# Solução 1: Reinstalar OpenCV
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python==4.8.1.78

# Solução 2: Instalar contrib
pip install opencv-contrib-python==4.8.1.78

# Solução 3: Verificar conflitos
pip list | grep opencv
```

### Problema: `ModuleNotFoundError: No module named 'sklearn'`

```bash
# Instalar scikit-learn
pip install scikit-learn>=1.3.0

# Verificar
python3 -c "import sklearn; print(sklearn.__version__)"
```

### Problema: Erro de compilação no Linux

```bash
# Instalar dependências de desenvolvimento
# Ubuntu/Debian:
sudo apt install build-essential python3-dev

# CentOS/RHEL:
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

### Problema: Versão do Python muito antiga

```bash
# Verificar versão
python3 --version

# Ubuntu: instalar versão específica
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS: usar pyenv
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

### Problema: Permissões no macOS

```bash
# Para câmera
# Vá em Configurações > Privacidade > Câmera > Autorize Terminal

# Para arquivos
sudo chown -R $(whoami) /caminho/do/projeto
```

### Problema: Ambiente virtual não ativa

```bash
# Verificar se está no diretório correto
pwd

# Recriar ambiente
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Windows
venv\Scripts\activate
```

## 🔧 Configuração Avançada

### GPU Support (Experimental)

```bash
# NVIDIA CUDA (Linux)
pip install tensorflow-gpu

# Apple Metal (macOS M1/M2)
pip install tensorflow-metal

# Verificar
python3 -c "
import tensorflow as tf
print('GPUs disponíveis:', tf.config.list_physical_devices('GPU'))
"
```

### Desenvolvimento

```bash
# Dependências extras para desenvolvimento
pip install pytest pytest-cov black flake8 jupyter

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Docker (Experimental)

```dockerfile
# Dockerfile de exemplo
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python3", "src/main.py"]
```

### Variáveis de Ambiente

```bash
# .bashrc ou .zshrc
export GRASS_DETECTOR_LOG_LEVEL=INFO
export GRASS_DETECTOR_OUTPUT_DIR=/caminho/personalizado
export GRASS_DETECTOR_CONFIG_FILE=config.json
```

### Performance Tuning

```bash
# OpenCV com otimizações
pip uninstall opencv-python
pip install opencv-contrib-python-headless

# NumPy com BLAS otimizado (Linux)
pip uninstall numpy
pip install numpy[mkl]

# Usar SSD para cache
export GRASS_DETECTOR_CACHE_DIR=/ssd/cache
```

## 📊 Verificação Final

Após a instalação, execute esta verificação completa:

```bash
#!/bin/bash
echo "🔍 Verificação completa da instalação..."

# 1. Verificar Python
echo "Python: $(python3 --version)"

# 2. Verificar ambiente virtual
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Ambiente virtual ativo: $VIRTUAL_ENV"
else
    echo "⚠️  Ambiente virtual não ativo"
fi

# 3. Verificar dependências
python3 -c "
try:
    import cv2, numpy, sklearn, scipy, matplotlib, PIL
    print('✅ Dependências principais: OK')
except ImportError as e:
    print(f'❌ Erro: {e}')
"

# 4. Verificar módulo principal
python3 -c "
import sys
sys.path.append('src')
try:
    from detector import GrassDetector
    print('✅ Módulo principal: OK')
except ImportError as e:
    print(f'❌ Erro no módulo: {e}')
"

# 5. Verificar diretórios
for dir in output models logs; do
    if [[ -d "$dir" ]]; then
        echo "✅ Diretório $dir: existe"
    else
        echo "⚠️  Diretório $dir: não encontrado"
    fi
done

# 6. Verificar exemplos
if [[ -f "examples/exemplo_mato_alto.jpg" ]]; then
    echo "✅ Imagens de exemplo: disponíveis"
else
    echo "⚠️  Imagens de exemplo: não encontradas"
fi

echo ""
echo "🎉 Verificação concluída!"
echo "Execute: python3 src/main.py --help"
```

## 📞 Suporte

Se encontrar problemas não cobertos aqui:

1. **Verifique os logs**: `logs/grass_detector.log`
2. **Execute com debug**: `GRASS_DETECTOR_LOG_LEVEL=DEBUG python3 src/main.py`
3. **Consulte o README**: Seção "Solução de Problemas"
4. **Reporte bugs**: [Link para issues do GitHub]

---

**Instalação bem-sucedida?** Execute `python3 src/main.py` e comece a usar! 🌿