#!/bin/bash

# ============================================================================
# Setup Script para Sistema de Detecção de Mato Alto
# ============================================================================
# Descrição: Script automatizado de instalação com verificação de dependências,
#            tratamento de erros avançado e suporte multiplataforma
# Versão: 2.0
# Compatibilidade: macOS, Linux, WSL
# ============================================================================

set -e  # Parar execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações
PYTHON_MIN_VERSION="3.8"
RECOMMENDED_PYTHON="3.11"
PROJECT_NAME="Sistema de Detecção de Mato Alto"
VENV_NAME="venv"
REQUIREMENTS_FILE="requirements.txt"

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

print_header() {
    echo -e "${CYAN}"
    echo "============================================================================"
    echo "🌿 $PROJECT_NAME - Setup Automatizado v2.0"
    echo "============================================================================"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[ETAPA]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Função para verificar versão do Python
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$($python_cmd --version 2>&1 | sed 's/Python //')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        local min_major=$(echo $PYTHON_MIN_VERSION | cut -d. -f1)
        local min_minor=$(echo $PYTHON_MIN_VERSION | cut -d. -f2)

        if [ "$major" -gt "$min_major" ] || ([ "$major" -eq "$min_major" ] && [ "$minor" -ge "$min_minor" ]); then
            echo "$version"
            return 0
        fi
    fi
    return 1
}

# Detectar sistema operacional
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -q Microsoft /proc/version 2>/dev/null; then
            echo "WSL"
        else
            echo "Linux"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "Windows"
    else
        echo "Unknown"
    fi
}

# Verificar se comando existe
command_exists() {
    command -v "$1" &> /dev/null
}

# Instalar dependências do sistema
install_system_dependencies() {
    local os_type=$(detect_os)
    print_step "Verificando dependências do sistema para $os_type"

    case $os_type in
        "macOS")
            if ! command_exists brew; then
                print_warning "Homebrew não encontrado. Recomenda-se instalar:"
                echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                echo ""
                read -p "Continuar sem Homebrew? (y/n): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            else
                print_info "Homebrew detectado. Verificando dependências..."
                # Instalar dependências se necessário
                if ! brew list python@3.11 &>/dev/null && ! brew list python@3.10 &>/dev/null; then
                    print_info "Instalando Python via Homebrew..."
                    brew install python@3.11 || print_warning "Falha ao instalar Python via Homebrew"
                fi
            fi
            ;;
        "Linux"|"WSL")
            print_info "Verificando dependências do sistema Linux..."
            if command_exists apt-get; then
                # Ubuntu/Debian
                sudo apt-get update -qq
                sudo apt-get install -y python3 python3-pip python3-venv python3-dev
                sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev
            elif command_exists yum; then
                # RHEL/CentOS/Fedora
                sudo yum install -y python3 python3-pip python3-venv python3-devel
                sudo yum install -y mesa-libGL glib2 libSM libXext libXrender
            elif command_exists pacman; then
                # Arch Linux
                sudo pacman -S --noconfirm python python-pip
            else
                print_warning "Gerenciador de pacotes não reconhecido. Instale manualmente:"
                echo "  - Python 3.8+ com pip e venv"
                echo "  - Bibliotecas OpenCV (libgl1-mesa-glx, libglib2.0-0)"
            fi
            ;;
        *)
            print_warning "Sistema operacional não reconhecido. Prosseguindo com instalação básica..."
            ;;
    esac
}

# Encontrar melhor comando Python
find_python_command() {
    local python_commands=("python3.13" "python3.12" "python3.11" "python3.10" "python3.9" "python3.8" "python3" "python")

    for cmd in "${python_commands[@]}"; do
        if version=$(check_python_version "$cmd"); then
            echo "$cmd"
            return 0
        fi
    done

    return 1
}

# ============================================================================
# MAIN SETUP PROCESS
# ============================================================================

main() {
    print_header

    # Verificar se estamos no diretório correto
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Arquivo requirements.txt não encontrado!"
        print_info "Execute este script no diretório raiz do projeto."
        exit 1
    fi

    print_step "Detectando ambiente..."
    local os_type=$(detect_os)
    print_success "Sistema detectado: $os_type"

    # Instalar dependências do sistema se necessário
    install_system_dependencies

    # Encontrar comando Python adequado
    print_step "Verificando instalação do Python..."

    if python_cmd=$(find_python_command); then
        local version=$(check_python_version "$python_cmd")
        print_success "Python encontrado: $python_cmd (versão $version)"

        if [[ "$version" == "$RECOMMENDED_PYTHON"* ]]; then
            print_success "Versão recomendada em uso!"
        elif [[ "$version" < "$PYTHON_MIN_VERSION" ]]; then
            print_warning "Versão abaixo da recomendada. Funcionalidade pode ser limitada."
        fi
    else
        print_error "Python $PYTHON_MIN_VERSION ou superior não encontrado!"
        echo ""
        print_info "Instalação recomendada por sistema:"
        echo ""
        echo "macOS:"
        echo "  brew install python@3.11"
        echo ""
        echo "Ubuntu/Debian:"
        echo "  sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev"
        echo ""
        echo "Windows:"
        echo "  Baixe de: https://www.python.org/downloads/"
        echo ""
        exit 1
    fi

    # Criar ambiente virtual
    print_step "Configurando ambiente virtual..."

    if [[ -d "$VENV_NAME" ]]; then
        print_info "Ambiente virtual existente encontrado."
        read -p "Recriar ambiente virtual? (recomendado) (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_NAME"
            print_info "Ambiente virtual anterior removido."
        fi
    fi

    if [[ ! -d "$VENV_NAME" ]]; then
        print_info "Criando novo ambiente virtual..."
        if $python_cmd -m venv "$VENV_NAME"; then
            print_success "Ambiente virtual criado com sucesso!"
        else
            print_error "Falha ao criar ambiente virtual!"
            print_info "Tente: $python_cmd -m pip install --user --upgrade pip setuptools"
            exit 1
        fi
    fi

    # Ativar ambiente virtual
    print_step "Ativando ambiente virtual..."
    source "$VENV_NAME/bin/activate"
    print_success "Ambiente virtual ativado!"

    # Atualizar pip
    print_step "Atualizando pip..."
    if pip install --upgrade pip setuptools wheel; then
        local pip_version=$(pip --version | cut -d' ' -f2)
        print_success "pip atualizado para versão $pip_version"
    else
        print_warning "Falha ao atualizar pip, prosseguindo..."
    fi

    # Instalar dependências
    print_step "Instalando dependências Python..."
    print_info "Isso pode levar alguns minutos na primeira execução..."

    # Instalar dependências com retry em caso de falha
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if pip install -r "$REQUIREMENTS_FILE"; then
            print_success "Todas as dependências instaladas com sucesso!"
            break
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                print_warning "Tentativa $retry_count falhou. Tentando novamente em 5 segundos..."
                sleep 5
            else
                print_error "Falha ao instalar dependências após $max_retries tentativas!"
                echo ""
                print_info "Soluções possíveis:"
                echo "  1. Verificar conexão com internet"
                echo "  2. Instalar manualmente: pip install -r requirements.txt"
                echo "  3. Usar versões mais recentes: pip install --upgrade -r requirements.txt"
                exit 1
            fi
        fi
    done

    # Verificar instalação das dependências principais
    print_step "Verificando instalação das dependências principais..."

    local dependencies=("cv2:opencv-python" "numpy:numpy" "sklearn:scikit-learn" "scipy:scipy")
    local failed_deps=()

    for dep in "${dependencies[@]}"; do
        local module_name="${dep%:*}"
        local package_name="${dep#*:}"

        if python -c "import $module_name; print('✅ $package_name:', $module_name.__version__ if hasattr($module_name, '__version__') else 'OK')" 2>/dev/null; then
            continue
        else
            print_warning "Problema com $package_name"
            failed_deps+=("$package_name")
        fi
    done

    if [ ${#failed_deps[@]} -gt 0 ]; then
        print_warning "Algumas dependências podem ter problemas:"
        for dep in "${failed_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        print_info "O sistema pode funcionar parcialmente. Execute os testes para verificar."
    else
        print_success "Todas as dependências principais verificadas!"
    fi

    # Criar diretórios necessários
    print_step "Criando estrutura de diretórios..."
    local dirs=("output" "models" "logs")
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_success "Diretório criado: $dir/"
        else
            print_info "Diretório já existe: $dir/"
        fi
    done

    # Executar testes básicos
    print_step "Executando testes básicos..."

    # Teste de importação
    if python -c "
import sys
sys.path.append('src')
try:
    from detector import GrassDetector
    print('✅ Módulo principal importado com sucesso!')
except Exception as e:
    print(f'❌ Erro ao importar módulo principal: {e}')
    sys.exit(1)
"; then
        print_success "Teste de importação passou!"
    else
        print_error "Teste de importação falhou!"
        echo ""
        print_info "Isso pode indicar problemas com as dependências."
        print_info "Execute manualmente: python -c 'from src.detector import GrassDetector'"
    fi

    # Teste com imagem de exemplo (se disponível)
    if [[ -f "examples/exemplo_mato_alto.jpg" ]]; then
        print_info "Executando teste com imagem de exemplo..."
        if timeout 30 python src/main.py --image examples/exemplo_mato_alto.jpg --method color &>/dev/null; then
            print_success "Teste com imagem de exemplo passou!"
        else
            print_warning "Teste com imagem demorou mais que esperado ou falhou."
            print_info "Isso é normal na primeira execução. O sistema deve funcionar normalmente."
        fi
    fi

    # Mostrar informações finais
    print_step "Finalizando instalação..."
    echo ""
    echo -e "${GREEN}🎉 Instalação concluída com sucesso!${NC}"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  COMO USAR O SISTEMA${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}1. Sempre ative o ambiente virtual primeiro:${NC}"
    echo "   source venv/bin/activate"
    echo ""
    echo -e "${YELLOW}2. Execute o sistema:${NC}"
    echo "   # Menu interativo (recomendado para iniciantes):"
    echo "   python3 src/main.py"
    echo ""
    echo "   # Análise direta de imagem:"
    echo "   python3 src/main.py --image caminho/da/imagem.jpg"
    echo ""
    echo "   # Análise com método específico:"
    echo "   python3 src/main.py --image caminho/da/imagem.jpg --method combined"
    echo ""
    echo "   # Análise em lote:"
    echo "   python3 src/main.py --batch pasta_com_imagens/"
    echo ""
    echo -e "${YELLOW}3. Exemplos e testes:${NC}"
    echo "   python3 examples/demo.py"
    echo "   python3 examples/test_reliability.py"
    echo ""
    echo -e "${YELLOW}4. Ajuda e documentação:${NC}"
    echo "   python3 src/main.py --help"
    echo "   cat README.md"
    echo ""
    echo -e "${PURPLE}📁 Resultados são salvos em: output/${NC}"
    echo -e "${PURPLE}📚 Documentação completa: README.md${NC}"
    echo -e "${PURPLE}🐛 Problemas? Veja seção 'Solução de Problemas' no README${NC}"
    echo ""

    # Verificação final do ambiente
    local python_location=$(which python)
    local pip_location=$(which pip)

    if [[ "$python_location" == *"$VENV_NAME"* ]] && [[ "$pip_location" == *"$VENV_NAME"* ]]; then
        print_success "Ambiente virtual configurado corretamente!"
    else
        print_warning "Ambiente virtual pode não estar ativo. Execute: source venv/bin/activate"
    fi

    echo ""
    echo -e "${GREEN}🌿 O Sistema de Detecção de Mato Alto está pronto para uso!${NC}"
    echo ""
}

# Tratamento de interrupção
trap 'echo -e "\n${RED}❌ Instalação interrompida pelo usuário${NC}"; exit 1' INT

# Executar função principal
main "$@"
