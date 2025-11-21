#!/bin/bash

# ============================================================================
# SCRIPT DE INSTALAÇÃO AUTOMATIZADO PARA RASPBERRY PI 4
# Sistema de Detecção com GPS e Upload Automático
# ============================================================================
# Uso: chmod +x install_rpi.sh && ./install_rpi.sh
# ============================================================================

set -e  # Para em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para print colorido
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Verifica se está rodando no Raspberry Pi
check_raspberry_pi() {
    print_header "VERIFICANDO SISTEMA"

    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        echo "Modelo detectado: $MODEL"

        if [[ $MODEL == *"Raspberry Pi"* ]]; then
            print_success "Raspberry Pi detectado!"
        else
            print_warning "Este script foi otimizado para Raspberry Pi"
            read -p "Continuar mesmo assim? (s/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Ss]$ ]]; then
                exit 1
            fi
        fi
    else
        print_warning "Não foi possível detectar o modelo do sistema"
    fi
}

# Atualiza sistema
update_system() {
    print_header "ATUALIZANDO SISTEMA"

    print_info "Atualizando lista de pacotes..."
    sudo apt-get update

    print_info "Atualizando pacotes instalados..."
    sudo apt-get upgrade -y

    print_success "Sistema atualizado!"
}

# Instala dependências do sistema
install_system_dependencies() {
    print_header "INSTALANDO DEPENDÊNCIAS DO SISTEMA"

    print_info "Instalando ferramentas essenciais..."
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        python3-setuptools \
        git \
        build-essential \
        cmake \
        pkg-config

    print_info "Instalando bibliotecas de desenvolvimento..."
    sudo apt-get install -y \
        libatlas-base-dev \
        libopenblas-dev \
        liblapack-dev \
        gfortran \
        libhdf5-dev

    print_info "Instalando OpenCV e dependências..."
    sudo apt-get install -y \
        python3-opencv \
        libopencv-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev

    print_info "Instalando NumPy e SciPy pré-compilados (ARM)..."
    sudo apt-get install -y \
        python3-numpy \
        python3-scipy

    print_success "Dependências do sistema instaladas!"
}

# Instala e configura GPS
install_gps() {
    print_header "CONFIGURANDO GPS"

    read -p "Você tem um módulo GPS conectado? (s/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_info "Instalando gpsd..."
        sudo apt-get install -y gpsd gpsd-clients python3-gps

        print_info "Configurando gpsd..."

        # Backup da configuração original
        if [ -f /etc/default/gpsd ]; then
            sudo cp /etc/default/gpsd /etc/default/gpsd.backup
        fi

        # Detecta dispositivo GPS
        print_info "Detectando dispositivos GPS..."
        GPS_DEVICE=""

        if [ -e /dev/ttyAMA0 ]; then
            GPS_DEVICE="/dev/ttyAMA0"
            print_info "GPS UART detectado: $GPS_DEVICE"
        elif [ -e /dev/ttyUSB0 ]; then
            GPS_DEVICE="/dev/ttyUSB0"
            print_info "GPS USB detectado: $GPS_DEVICE"
        elif [ -e /dev/ttyACM0 ]; then
            GPS_DEVICE="/dev/ttyACM0"
            print_info "GPS ACM detectado: $GPS_DEVICE"
        else
            print_warning "Nenhum dispositivo GPS detectado automaticamente"
            read -p "Digite o caminho do dispositivo GPS (ex: /dev/ttyAMA0): " GPS_DEVICE
        fi

        # Configura gpsd
        sudo bash -c "cat > /etc/default/gpsd << EOF
# Default settings for gpsd
START_DAEMON=\"true\"
GPSD_OPTIONS=\"-n\"
DEVICES=\"$GPS_DEVICE\"
USBAUTO=\"true\"
GPSD_SOCKET=\"/var/run/gpsd.sock\"
EOF"

        # Adiciona usuário ao grupo dialout (permissões serial)
        sudo usermod -a -G dialout $USER

        # Habilita e inicia gpsd
        sudo systemctl enable gpsd
        sudo systemctl start gpsd

        print_success "gpsd configurado e iniciado!"
        print_info "Teste com: cgps -s"
        print_warning "Você pode precisar fazer logout e login para aplicar permissões do grupo dialout"
    else
        print_info "Pulando configuração de GPS (modo MOCK será usado)"
        print_info "Para instalar GPS depois:"
        echo "  sudo apt-get install gpsd gpsd-clients python3-gps"
        echo "  sudo systemctl enable gpsd && sudo systemctl start gpsd"
    fi
}

# Instala dependências Python
install_python_dependencies() {
    print_header "INSTALANDO DEPENDÊNCIAS PYTHON"

    print_info "Atualizando pip..."
    python3 -m pip install --upgrade pip

    print_info "Instalando pacotes Python..."

    # Instala do requirements_rpi.txt
    if [ -f requirements_rpi.txt ]; then
        print_info "Usando requirements_rpi.txt (otimizado para Raspberry Pi)..."
        python3 -m pip install -r requirements_rpi.txt --no-cache-dir
    else
        print_warning "requirements_rpi.txt não encontrado, instalando pacotes individuais..."
        python3 -m pip install --no-cache-dir \
            opencv-python-headless \
            numpy \
            scipy \
            scikit-learn \
            requests \
            gps3 \
            pyserial \
            python-dotenv \
            colorama
    fi

    print_success "Dependências Python instaladas!"
}

# Cria estrutura de diretórios
create_directories() {
    print_header "CRIANDO ESTRUTURA DE DIRETÓRIOS"

    mkdir -p captures
    mkdir -p queue
    mkdir -p logs
    mkdir -p output

    print_success "Diretórios criados:"
    echo "  - captures/  (imagens capturadas temporárias)"
    echo "  - queue/     (fila de upload offline)"
    echo "  - logs/      (arquivos de log)"
    echo "  - output/    (saída opcional)"
}

# Configura arquivo de configuração
setup_config() {
    print_header "CONFIGURANDO SISTEMA"

    if [ ! -f config_rpi.json ]; then
        print_error "config_rpi.json não encontrado!"
        print_info "Certifique-se de que o arquivo existe e está no diretório correto"
        return 1
    fi

    print_info "Arquivo config_rpi.json encontrado"
    print_warning "IMPORTANTE: Edite config_rpi.json e configure:"
    echo "  1. URL da API em 'api.url'"
    echo "  2. API key em 'api.key' (se necessário)"
    echo "  3. Backend GPS em 'gps.backend' (gpsd, serial ou mock)"
    echo "  4. Tipo de detecção em 'detector.type' (pothole ou grass)"
    echo ""
    echo "Exemplo: nano config_rpi.json"
}

# Configura serviço systemd (opcional)
setup_systemd_service() {
    print_header "CONFIGURAR SERVIÇO SYSTEMD (OPCIONAL)"

    read -p "Deseja criar um serviço systemd para iniciar automaticamente no boot? (s/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Ss]$ ]]; then
        CURRENT_DIR=$(pwd)
        CURRENT_USER=$(whoami)

        print_info "Criando serviço systemd..."

        sudo bash -c "cat > /etc/systemd/system/detection-system.service << EOF
[Unit]
Description=Sistema de Detecção com GPS e Upload Automático
After=network.target gpsd.service
Wants=gpsd.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/src/rpi/main_rpi.py --config $CURRENT_DIR/config_rpi.json --mode continuous
Restart=always
RestartSec=10
StandardOutput=append:$CURRENT_DIR/logs/system.log
StandardError=append:$CURRENT_DIR/logs/system_error.log

[Install]
WantedBy=multi-user.target
EOF"

        sudo systemctl daemon-reload
        sudo systemctl enable detection-system.service

        print_success "Serviço systemd criado!"
        print_info "Comandos úteis:"
        echo "  sudo systemctl start detection-system    # Iniciar"
        echo "  sudo systemctl stop detection-system     # Parar"
        echo "  sudo systemctl status detection-system   # Status"
        echo "  sudo systemctl restart detection-system  # Reiniciar"
        echo "  journalctl -u detection-system -f        # Ver logs em tempo real"
    else
        print_info "Pulando configuração de serviço systemd"
    fi
}

# Testa instalação
test_installation() {
    print_header "TESTANDO INSTALAÇÃO"

    print_info "Verificando Python..."
    python3 --version

    print_info "Verificando módulos Python..."
    python3 -c "import cv2; print('✓ OpenCV:', cv2.__version__)"
    python3 -c "import numpy; print('✓ NumPy:', numpy.__version__)"
    python3 -c "import requests; print('✓ Requests instalado')"

    if command -v gpsd &> /dev/null; then
        print_info "Verificando GPS..."
        sudo systemctl status gpsd --no-pager || true
    fi

    print_success "Testes básicos concluídos!"
}

# Exibe informações finais
show_final_info() {
    print_header "INSTALAÇÃO CONCLUÍDA!"

    echo -e "${GREEN}✅ Sistema instalado com sucesso!${NC}\n"

    print_info "PRÓXIMOS PASSOS:"
    echo ""
    echo "1. Configure o sistema:"
    echo "   ${YELLOW}nano config_rpi.json${NC}"
    echo ""
    echo "2. Execute o sistema:"
    echo "   ${YELLOW}python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous${NC}"
    echo ""
    echo "3. Ou teste com uma imagem:"
    echo "   ${YELLOW}python3 src/rpi/main_rpi.py --config config_rpi.json --mode single --image foto.jpg${NC}"
    echo ""

    print_info "COMANDOS ÚTEIS:"
    echo "  cgps -s                    # Testar GPS"
    echo "  vcgencmd measure_temp      # Ver temperatura do CPU"
    echo "  htop                       # Monitorar recursos"
    echo ""

    print_info "LOGS:"
    echo "  tail -f detection_system.log"
    echo "  tail -f logs/system.log"
    echo ""

    print_warning "IMPORTANTE:"
    echo "  - Edite config_rpi.json antes de executar!"
    echo "  - Se configurou GPS, faça logout/login para aplicar permissões"
    echo "  - Monitore temperatura do Raspberry Pi durante uso prolongado"
    echo ""

    print_success "Instalação finalizada! Boa sorte! 🚀"
}

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

main() {
    clear

    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║   INSTALADOR - SISTEMA DE DETECÇÃO RASPBERRY PI 4         ║"
    echo "║   Sistema com GPS e Upload Automático                     ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    print_warning "Este script irá instalar todas as dependências necessárias"
    print_warning "Tempo estimado: 15-30 minutos (dependendo da conexão)"
    echo ""
    read -p "Deseja continuar? (s/n) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Instalação cancelada."
        exit 0
    fi

    # Executa instalação
    check_raspberry_pi
    update_system
    install_system_dependencies
    install_gps
    install_python_dependencies
    create_directories
    setup_config
    setup_systemd_service
    test_installation
    show_final_info
}

# Executa script
main
