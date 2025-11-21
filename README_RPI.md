# 🍓 Sistema de Detecção - Raspberry Pi 4

Sistema **otimizado** para Raspberry Pi 4 com detecção automática, GPS integrado e upload para API com fila offline.

## 🎯 Características

✅ **Detecção Otimizada** - Algoritmos leves para ARM (pothole/grass)  
✅ **GPS Integrado** - Captura automática de latitude/longitude  
✅ **Upload Automático** - Envia dados + imagem para API  
✅ **Fila Offline** - Armazena detecções quando sem internet  
✅ **Retry Inteligente** - Reenvio automático com backoff  
✅ **Auto-cleanup** - Deleta imagens após upload bem-sucedido (200)  
✅ **Baixo Consumo** - Otimizado para performance em ARM  

## 📋 Requisitos

### Hardware
- **Raspberry Pi 4 Model B** (2GB+ RAM recomendado)
- **Câmera** (USB, Pi Camera Module ou compatível)
- **Módulo GPS** (UART/USB - opcional, tem modo mock)
- **Cartão SD** (16GB+ recomendado)
- **Conexão internet** (WiFi/Ethernet - pode ser intermitente)

### Software
- **Raspberry Pi OS** (Bullseye/Bookworm)
- **Python 3.8+**
- Dependências instaladas via `install_rpi.sh`

## 🚀 Instalação Rápida

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd computacional-vision
```

### 2. Execute o instalador

```bash
chmod +x install_rpi.sh
./install_rpi.sh
```

O instalador irá:
- ✓ Atualizar sistema
- ✓ Instalar dependências (OpenCV, NumPy, etc)
- ✓ Configurar GPS (gpsd)
- ✓ Criar estrutura de diretórios
- ✓ Configurar serviço systemd (opcional)

**Tempo estimado:** 15-30 minutos

### 3. Configure o sistema

Edite o arquivo de configuração:

```bash
nano config_rpi.json
```

**Configurações obrigatórias:**

```json
{
  "api": {
    "url": "https://sua-api.com/api",
    "key": "sua-chave-api-se-necessario"
  },
  "gps": {
    "backend": "gpsd",
    "device": "/dev/ttyAMA0"
  },
  "detector": {
    "type": "pothole",
    "min_confidence": 0.5
  }
}
```

## 🎮 Como Usar

### Modo Contínuo (Recomendado)

Captura e processa imagens continuamente:

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous
```

### Modo Imagem Única

Processa uma imagem específica:

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode single --image foto.jpg
```

### Como Serviço (Auto-start)

Se configurou o serviço systemd durante instalação:

```bash
# Iniciar serviço
sudo systemctl start detection-system

# Parar serviço
sudo systemctl stop detection-system

# Ver status
sudo systemctl status detection-system

# Ver logs em tempo real
journalctl -u detection-system -f
```

## 📊 Fluxo de Funcionamento

```
┌─────────────┐
│   Câmera    │
└──────┬──────┘
       │ Captura (intervalo configurável)
       ▼
┌─────────────┐
│  Detector   │ ◄─── Redimensiona para otimização (640px)
└──────┬──────┘
       │ Detecta (pothole/grass)
       ▼
┌─────────────┐
│     GPS     │ ◄─── Obtém coordenadas
└──────┬──────┘
       │
       ▼
   Detectado?
       │
   ┌───┴───┐
   │  SIM  │               │  NÃO  │
   ▼       │               ▼       │
┌─────────────┐      ┌──────────┐
│ Adiciona    │      │  Deleta  │
│ à Fila      │      │  Imagem  │
└──────┬──────┘      └──────────┘
       │
       ▼
┌─────────────┐
│ Monitor de  │ ◄─── Verifica conexão (10s)
│    Rede     │
└──────┬──────┘
       │
   Conectado?
       │
   ┌───┴───┐
   │  SIM  │               │  NÃO  │
   ▼       │               ▼       │
┌─────────────┐      ┌──────────┐
│ Upload para │      │ Mantém   │
│    API      │      │ na Fila  │
└──────┬──────┘      └──────────┘
       │
   Status 200?
       │
   ┌───┴───┐
   │  SIM  │               │  NÃO  │
   ▼       │               ▼       │
┌─────────────┐      ┌──────────┐
│   Deleta    │      │  Retry   │
│   Imagem    │      │ (max 3x) │
└─────────────┘      └──────────┘
```

## 🔧 Configurações Importantes

### Tipos de Detecção

```json
"detector": {
  "type": "pothole",  // ou "grass" para mato alto
  "min_confidence": 0.5,  // 0.0 - 1.0
  "resize_width": 640  // pixels (otimização)
}
```

### Intervalo de Captura

```json
"capture_interval": 5.0  // segundos entre capturas
```

**Presets recomendados:**

| Cenário | Intervalo | Confiança | Resolução |
|---------|-----------|-----------|-----------|
| Urbano | 3s | 0.6 | 640px |
| Rodovia | 2s | 0.5 | 800px |
| Economia | 10s | 0.7 | 480px |

### GPS Backend

```json
"gps": {
  "backend": "gpsd",    // "gpsd", "serial" ou "mock"
  "device": "/dev/ttyAMA0",  // Para UART
  "baudrate": 9600
}
```

**Dispositivos GPS comuns:**
- `/dev/ttyAMA0` - GPIO UART (pinos 8/10)
- `/dev/ttyUSB0` - GPS USB
- `/dev/ttyACM0` - GPS USB (ACM)

### API Endpoint

O sistema envia POST request para `{api_url}/detections` com:

**Form Data:**
```json
{
  "latitude": -23.550520,
  "longitude": -46.633308,
  "confidence": 0.87,
  "timestamp": 1706234567.89,
  "altitude": 750.0,
  "detection_type": "pothole"
}
```

**File:**
```
image: [arquivo JPEG]
```

**Headers (se configurado):**
```
Authorization: Bearer {api_key}
```

## 📁 Estrutura de Diretórios

```
computacional-vision/
├── src/rpi/              # Código otimizado para RPi
│   ├── main_rpi.py       # Sistema principal
│   ├── gps_handler.py    # GPS (gpsd/serial/mock)
│   ├── simple_detector.py # Detector otimizado
│   ├── api_client.py     # Cliente API + fila
│   └── network_monitor.py # Monitor de conexão
├── config_rpi.json       # Configuração
├── requirements_rpi.txt  # Dependências otimizadas
├── install_rpi.sh        # Instalador automático
├── captures/             # Imagens temporárias
├── queue/                # Fila offline (persistente)
└── logs/                 # Arquivos de log
```

## 🧪 Testes

### Testar GPS

```bash
# Ver status do gpsd
sudo systemctl status gpsd

# Interface gráfica GPS
cgps -s

# Dados raw
gpspipe -w
```

### Testar Detecção

```bash
# Teste rápido com imagem
python3 -c "
from src.rpi.simple_detector import quick_detect
detected, conf = quick_detect('foto.jpg', 'pothole', save_output=True)
print(f'Detectado: {detected}, Confiança: {conf:.2f}')
"
```

### Testar Conexão

```bash
# Verificação rápida
python3 -c "
from src.rpi.network_monitor import quick_check_connection
print('Conectado!' if quick_check_connection() else 'Sem conexão')
"
```

## 📈 Monitoramento

### Ver Logs

```bash
# Log principal
tail -f detection_system.log

# Log do serviço
journalctl -u detection-system -f

# Últimas 100 linhas
tail -n 100 detection_system.log
```

### Estatísticas

O sistema exibe estatísticas a cada ciclo:

```
📊 ESTATÍSTICAS
────────────────────────────────────────
  📷 Capturas: 142
  🎯 Detecções: 37
  📤 Enviados: 35
  📋 Na fila: 2
  ❌ Erros: 0
  🌐 Conexão: ✓
────────────────────────────────────────
```

### Monitorar Recursos

```bash
# CPU/RAM/Temperatura
htop

# Temperatura do CPU
vcgencmd measure_temp

# Uso de disco
df -h

# Espaço na fila
du -sh queue/
```

## ⚡ Otimizações de Performance

### 1. Reduzir Resolução
```json
"detector": {
  "resize_width": 480  // Mais rápido, menos preciso
}
```

### 2. Aumentar Intervalo
```json
"capture_interval": 10.0  // Menos capturas
```

### 3. Desabilitar Anotações
```json
"save_annotated": false  // Economiza I/O
```

### 4. Limitar Threads OpenCV
```bash
export OPENCV_NUM_THREADS=2
```

### 5. Overclock (Cuidado!)
```bash
# /boot/config.txt
over_voltage=2
arm_freq=1750
```

## 🔒 Segurança

### API Key

**NÃO commite a API key no Git!**

Use variável de ambiente:

```bash
export API_KEY="sua-chave-secreta"
```

Ou arquivo `.env`:

```bash
echo "API_KEY=sua-chave-secreta" > .env
```

Configure no `config_rpi.json`:

```json
"api": {
  "key": "${API_KEY}"  // Será substituído
}
```

### Permissões

```bash
# Adicionar usuário ao grupo camera (Pi Camera)
sudo usermod -a -G video $USER

# Adicionar usuário ao grupo dialout (GPS serial)
sudo usermod -a -G dialout $USER

# Aplicar permissões (logout necessário)
```

## 🐛 Troubleshooting

### Erro: Câmera não encontrada

```bash
# Listar câmeras
v4l2-ctl --list-devices

# Testar câmera
raspistill -o test.jpg  # Pi Camera
fswebcam test.jpg       # USB Camera
```

### Erro: GPS sem fix

```bash
# Verificar conexão
cgps -s

# Verificar dispositivo
ls -l /dev/tty*

# Reiniciar gpsd
sudo systemctl restart gpsd
```

### Erro: Sem conexão com API

```bash
# Testar conectividade
ping -c 3 8.8.8.8

# Testar API
curl -X POST https://sua-api.com/api/detections

# Verificar fila
ls -lh queue/
```

### Erro: Memória insuficiente

```bash
# Aumentar swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Verificar
free -h
```

### Erro: CPU muito quente

```bash
# Ver temperatura
vcgencmd measure_temp

# Se > 80°C:
# 1. Adicione dissipador/cooler
# 2. Reduza resolução
# 3. Aumente intervalo de captura
# 4. Remova overclock
```

## 📚 Exemplos de Uso

### Exemplo 1: Detecção de Buracos em Rodovia

```json
{
  "detector": {
    "type": "pothole",
    "min_confidence": 0.5,
    "resize_width": 800
  },
  "capture_interval": 2.0,
  "camera": {
    "width": 1920,
    "height": 1080
  }
}
```

### Exemplo 2: Detecção de Mato Alto em Área Urbana

```json
{
  "detector": {
    "type": "grass",
    "min_confidence": 0.6,
    "resize_width": 640
  },
  "capture_interval": 5.0,
  "camera": {
    "width": 1280,
    "height": 720
  }
}
```

### Exemplo 3: Modo Economia de Energia

```json
{
  "detector": {
    "type": "pothole",
    "min_confidence": 0.7,
    "resize_width": 480
  },
  "capture_interval": 10.0,
  "camera": {
    "width": 640,
    "height": 480
  },
  "performance": {
    "opencv_threads": 1,
    "low_power_mode": true
  }
}
```

## 🤝 Contribuindo

Melhorias são bem-vindas! Áreas de interesse:

- 🎯 Novos tipos de detecção
- 🚀 Otimizações de performance
- 🔌 Suporte a novos sensores
- 📱 Interface web/mobile
- 🧠 Modelos de ML mais precisos

## 📄 Licença

[Sua licença aqui]

## 💡 Suporte

- 📧 Email: seu-email@example.com
- 🐛 Issues: [GitHub Issues](seu-repo/issues)
- 📖 Wiki: [GitHub Wiki](seu-repo/wiki)

---

**Feito com ❤️ para Raspberry Pi 4**

🍓 Otimizado para ARM | 📡 GPS Integrado | 🌐 Fila Offline | 🚀 Performance