# 🍓 Módulo RPI - Sistema de Detecção para Raspberry Pi 4

Módulo otimizado para Raspberry Pi com detecção automática, GPS e upload para API.

## 📦 Componentes

### 🎯 main_rpi.py
**Sistema principal** - Orquestra todos os componentes.

```python
from src.rpi.main_rpi import DetectionSystemRPi

# Carrega configuração
config = load_config('config_rpi.json')

# Inicializa sistema
system = DetectionSystemRPi(config)

# Executa em modo contínuo
system.run_continuous()
```

**Funcionalidades:**
- Captura de imagens da câmera
- Processamento com detector
- Integração com GPS
- Upload automático para API
- Gerenciamento de fila offline

---

### 📡 gps_handler.py
**GPS Handler** - Gerencia coordenadas GPS com múltiplos backends.

```python
from src.rpi.gps_handler import GPSHandler, create_gps_handler

# Modo gpsd (recomendado para Raspberry Pi)
gps = GPSHandler(backend='gpsd')

# Obtém coordenadas
coords = gps.get_coordinates()
print(f"Lat: {coords.latitude}, Lon: {coords.longitude}")

# Aguarda fix GPS
if gps.wait_for_fix(timeout=60):
    print("GPS fix obtido!")
```

**Backends suportados:**
- `gpsd` - Daemon GPS (recomendado)
- `serial` - GPS serial direto (UART/USB)
- `mock` - Coordenadas fictícias para testes

**Exemplo de configuração:**
```json
{
  "gps": {
    "backend": "gpsd",
    "device": "/dev/ttyAMA0",
    "baudrate": 9600,
    "timeout": 5.0
  }
}
```

---

### 🔍 simple_detector.py
**Detector Otimizado** - Detecção leve e rápida para ARM.

```python
from src.rpi.simple_detector import SimpleDetector, quick_detect

# Inicializa detector
detector = SimpleDetector(
    detection_type='pothole',  # ou 'grass'
    min_confidence=0.5,
    resize_width=640
)

# Detecta
detected, confidence, annotated = detector.detect('image.jpg')

if detected:
    print(f"Detectado! Confiança: {confidence:.2f}")
    detector.save_annotated_image(annotated, 'output.jpg')
```

**Tipos de detecção:**
- `pothole` - Detecção de buracos (usando análise de bordas)
- `grass` - Detecção de mato alto (usando análise de cor HSV)

**Otimizações:**
- Redimensionamento antes do processamento
- Algoritmos leves (sem deep learning)
- Sem GUI (headless)

---

### 🌐 api_client.py
**Cliente API** - Upload com fila offline e retry automático.

```python
from src.rpi.api_client import APIClient
from src.rpi.gps_handler import GPSCoordinates

# Inicializa cliente
client = APIClient(
    api_url='https://sua-api.com/api',
    api_key='sua-chave',
    auto_process=True
)

# Adiciona detecção à fila
coords = GPSCoordinates(latitude=-23.55, longitude=-46.63)
client.add_detection(
    image_path='buraco.jpg',
    coordinates=coords,
    confidence=0.87,
    detection_type='pothole'
)

# Processa fila manualmente (ou deixe o auto_process fazer)
client.process_queue()

# Ver estatísticas
stats = client.get_stats()
print(f"Enviados: {stats['total_sent']}, Na fila: {stats['queue_size']}")
```

**Funcionalidades:**
- ✅ Fila persistente em disco
- ✅ Retry automático (até 3 tentativas)
- ✅ Verificação de conexão
- ✅ Processamento em background
- ✅ Deleta imagem após sucesso (HTTP 200)

---

### 🔌 network_monitor.py
**Monitor de Rede** - Verifica conectividade de forma eficiente.

```python
from src.rpi.network_monitor import NetworkMonitor, quick_check_connection

# Verificação rápida
if quick_check_connection():
    print("Conectado!")

# Monitor com callbacks
monitor = NetworkMonitor(check_interval=10.0)

def on_connect():
    print("Conexão estabelecida!")

def on_disconnect():
    print("Conexão perdida!")

monitor.on_connected(on_connect)
monitor.on_disconnected(on_disconnect)
monitor.start_monitoring()

# Aguarda conexão
if monitor.wait_for_connection(timeout=60):
    print("Internet disponível!")
```

**Características:**
- Verificação via socket (rápida)
- Cache de status
- Callbacks para mudanças de status
- Monitoramento em background

---

## 🚀 Uso Rápido

### Exemplo Completo

```python
#!/usr/bin/env python3
"""Exemplo completo de uso do módulo RPI"""

import sys
sys.path.insert(0, '../..')

from src.rpi.gps_handler import create_gps_handler
from src.rpi.simple_detector import SimpleDetector
from src.rpi.api_client import APIClient
from src.rpi.network_monitor import NetworkMonitor

# 1. Inicializa GPS
gps = create_gps_handler({'backend': 'mock'})
print("✓ GPS inicializado")

# 2. Inicializa detector
detector = SimpleDetector(detection_type='pothole')
print("✓ Detector inicializado")

# 3. Inicializa API client
api = APIClient(
    api_url='https://sua-api.com/api',
    api_key='sua-chave',
    auto_process=True
)
print("✓ API client inicializado")

# 4. Detecta imagem
detected, confidence, annotated = detector.detect('foto.jpg')

if detected:
    print(f"✓ Detecção positiva! Confiança: {confidence:.2f}")
    
    # 5. Obtém GPS
    coords = gps.get_coordinates()
    print(f"✓ GPS: ({coords.latitude:.6f}, {coords.longitude:.6f})")
    
    # 6. Envia para API
    api.add_detection(
        image_path='foto.jpg',
        coordinates=coords,
        confidence=confidence,
        detection_type='pothole'
    )
    print("✓ Adicionado à fila de upload")
else:
    print("⚪ Sem detecção")

# 7. Ver estatísticas
stats = api.get_stats()
print(f"\n📊 Estatísticas:")
print(f"  Enviados: {stats['total_sent']}")
print(f"  Na fila: {stats['queue_size']}")
print(f"  Conectado: {stats['connected']}")
```

---

## 📋 Dependências

```bash
# Instale via requirements_rpi.txt
pip3 install -r ../../requirements_rpi.txt

# Ou instale individualmente:
pip3 install opencv-python-headless numpy requests pyserial gps3
```

---

## 🧪 Testes

### Testar GPS

```bash
python3 -c "
from gps_handler import GPSHandler
gps = GPSHandler(backend='mock')
coords = gps.get_coordinates()
print(f'GPS: {coords.latitude}, {coords.longitude}')
"
```

### Testar Detector

```bash
python3 -c "
from simple_detector import quick_detect
detected, conf = quick_detect('../../foto.jpg', 'pothole', save_output=True)
print(f'Detectado: {detected}, Confiança: {conf:.2f}')
"
```

### Testar API Client

```bash
python3 -c "
from api_client import APIClient
from gps_handler import GPSCoordinates

client = APIClient('https://httpbin.org/post', auto_process=False)
coords = GPSCoordinates(latitude=-23.55, longitude=-46.63)

# Simula adição (use imagem real)
print(f'Fila: {client.get_queue_size()} itens')
"
```

### Testar Network Monitor

```bash
python3 -c "
from network_monitor import quick_check_connection
print('Conectado!' if quick_check_connection() else 'Sem conexão')
"
```

---

## 📁 Estrutura de Classes

### GPSHandler

```python
class GPSHandler:
    def __init__(backend, device, baudrate, timeout)
    def get_coordinates() -> GPSCoordinates
    def get_last_known_coordinates() -> GPSCoordinates
    def is_fix_available() -> bool
    def wait_for_fix(timeout) -> bool
    def close()
```

### SimpleDetector

```python
class SimpleDetector:
    def __init__(detection_type, min_confidence, resize_width)
    def detect(image_path) -> (bool, float, np.ndarray)
    def save_annotated_image(annotated, output_path, quality)
```

### APIClient

```python
class APIClient:
    def __init__(api_url, api_key, queue_dir, max_retries, auto_process)
    def add_detection(image_path, coordinates, confidence, detection_type)
    def send_detection(data) -> bool
    def process_queue(max_items) -> int
    def get_queue_size() -> int
    def get_stats() -> dict
    def start_auto_processing()
    def stop_auto_processing()
```

### NetworkMonitor

```python
class NetworkMonitor:
    def __init__(check_interval, timeout, check_hosts)
    def is_connected(force_check) -> bool
    def wait_for_connection(timeout) -> bool
    def start_monitoring()
    def stop_monitoring()
    def on_connected(callback)
    def on_disconnected(callback)
```

---

## ⚙️ Configuração

### Arquivo config_rpi.json

```json
{
  "api": {
    "url": "https://sua-api.com/api",
    "key": "sua-chave-api"
  },
  "gps": {
    "backend": "gpsd",
    "device": "/dev/ttyAMA0",
    "baudrate": 9600,
    "timeout": 5.0
  },
  "detector": {
    "type": "pothole",
    "min_confidence": 0.5,
    "resize_width": 640
  },
  "camera": {
    "index": 0,
    "width": 1280,
    "height": 720
  },
  "capture_interval": 5.0
}
```

---

## 🔧 Troubleshooting

### ImportError: No module named 'cv2'

```bash
pip3 install opencv-python-headless
# Ou use a versão do sistema:
sudo apt-get install python3-opencv
```

### GPS não funciona

```bash
# Verifique gpsd
sudo systemctl status gpsd

# Reinicie gpsd
sudo systemctl restart gpsd

# Use modo mock para testes
gps = GPSHandler(backend='mock')
```

### API não conecta

```bash
# Teste a URL
curl https://sua-api.com/api/detections

# Verifique a fila
ls -lh ../../queue/
```

---

## 📚 Documentação

- **../../README_RPI.md** - Documentação completa
- **../../QUICKSTART_RPI.md** - Guia rápido
- **../../API_EXAMPLES.md** - Exemplos de backend
- **../../config_rpi.json** - Configuração

---

## 🤝 Contribuindo

Este módulo é otimizado para Raspberry Pi. Ao contribuir:

1. Mantenha baixo consumo de CPU/RAM
2. Use algoritmos leves (evite deep learning)
3. Teste em hardware real (RPi 4)
4. Documente otimizações
5. Adicione testes

---

**🍓 Otimizado para Raspberry Pi 4**