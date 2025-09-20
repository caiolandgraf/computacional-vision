#!/bin/bash

# Script de instalação e setup para o Sistema de Detecção de Mato Alto
# Funciona no macOS com fish shell

echo "🌿 Configurando Sistema de Detecção de Mato Alto..."

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale o Python primeiro."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
echo "⬆️ Atualizando pip..."
pip install --upgrade pip

# Instala dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Verifica instalação das principais dependências
echo "🔍 Verificando instalação..."

python3 -c "import cv2; print('✅ OpenCV instalado:', cv2.__version__)" || echo "❌ Erro ao importar OpenCV"
python3 -c "import numpy; print('✅ NumPy instalado:', numpy.__version__)" || echo "❌ Erro ao importar NumPy"
python3 -c "import tensorflow; print('✅ TensorFlow instalado:', tensorflow.__version__)" || echo "❌ Erro ao importar TensorFlow"

# Cria diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p output
mkdir -p models

# Executa script de exemplo
echo "🧪 Executando teste básico..."
cd examples
python3 demo.py <<EOF
1
0
EOF
cd ..

echo ""
echo "🎉 Instalação concluída com sucesso!"
echo ""
echo "Para usar o sistema:"
echo "1. Ative o ambiente virtual: source venv/bin/activate"
echo "2. Execute: python3 src/main.py"
echo ""
echo "Ou use diretamente:"
echo "  python3 src/main.py --image caminho/da/imagem.jpg"
echo ""
echo "Para exemplos e testes:"
echo "  python3 examples/demo.py"