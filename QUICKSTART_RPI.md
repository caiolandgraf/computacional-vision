# 🚀 Quick Start - Raspberry Pi 4

Guia rápido para colocar o sistema funcionando em **menos de 30 minutos**.

## ⚡ Instalação Express (5 comandos)

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd computacional-vision

# 2. Execute o instalador
chmod +x install_rpi.sh
./install_rpi.sh

# 3. Configure a API
nano config_rpi.json
# Edite: api.url e api.key

# 4. Teste a instalação
python3 test_rpi.py

# 5. Execute!
python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous
```

## 📝 Configuração Mínima

Edite `config_rpi.json` e configure apenas 3 campos:

```json
{
  "api": {
    "url": "https://sua-api.com/api",  // ← OBRIGATÓRIO
    "key": "sua-chave-se-necessario"   // ← Opcional
  },
  "detector": {
    "type": "pothole"  // ← "pothole" ou "grass"
  }
}
```

Pronto! O resto usa valores padrão otimizados.

## 🎯 Cenários Comuns

### 1. Detecção de Buracos (padrão)

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous
```

Configuração padrão já está otimizada para buracos!

### 2. Detecção de Mato Alto

Edite `config_rpi.json`:

```json
{
  "detector": {
    "type": "grass"
  }
}
```

Execute:

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous
```

### 3. Teste com Imagem Única

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode single --image foto.jpg
```

### 4. Sem GPS (Modo Mock)

Se não tem GPS físico, use modo mock para testes:

```json
{
  "gps": {
    "backend": "mock"
  }
}
```

## 🔧 Ajustes Rápidos de Performance

### Mais Rápido (menos preciso)

```json
{
  "capture_interval": 10.0,
  "detector": {
    "resize_width": 480
  }
}
```

### Mais Preciso (mais lento)

```json
{
  "capture_interval": 2.0,
  "detector": {
    "resize_width": 800,
    "min_confidence": 0.7
  }
}
```

### Economia de Energia

```json
{
  "capture_interval": 15.0,
  "detector": {
    "resize_width": 320
  },
  "camera": {
    "width": 640,
    "height": 480
  }
}
```

## 📊 Como Funciona

```
Captura → Detecta → GPS → Fila → Upload → Deleta
   ↓         ↓       ↓      ↓       ↓       ↓
  5s        0.5s    0.1s   0ms     2s      0s
```

**Sem detecção?** Imagem é deletada imediatamente.  
**Sem internet?** Fica na fila até conectar.  
**Upload OK (200)?** Imagem é deletada automaticamente.

## 🌐 Especificação da API

Seu backend deve aceitar POST em `/detections`:

**Endpoint:**
```
POST {api_url}/detections
```

**Headers:**
```
Authorization: Bearer {api_key}  // Se configurado
Content-Type: multipart/form-data
```

**Body (form-data):**
```
latitude: -23.550520
longitude: -46.633308
confidence: 0.87
timestamp: 1706234567.89
altitude: 750.0
detection_type: "pothole"
image: [arquivo JPEG]
```

**Resposta esperada:**
```json
{
  "status": "success",
  "id": "12345"
}
```

**Códigos HTTP:**
- `200` - Sucesso (imagem será deletada)
- `4xx` - Erro do cliente (item é descartado após 3 tentativas)
- `5xx` - Erro do servidor (retry automático)

## 🧪 Testes Rápidos

### Testar tudo

```bash
python3 test_rpi.py
```

### Testar apenas GPS

```bash
cgps -s
```

### Testar apenas câmera

```bash
# USB camera
fswebcam test.jpg

# Pi Camera
raspistill -o test.jpg
```

### Testar apenas conexão

```bash
ping -c 3 8.8.8.8
```

### Testar apenas detecção

```bash
python3 -c "
from src.rpi.simple_detector import quick_detect
detected, conf = quick_detect('sua-foto.jpg', 'pothole', save_output=True)
print(f'Detectado: {detected}, Confiança: {conf:.2f}')
"
```

## 📈 Monitoramento

### Ver o que está acontecendo

```bash
tail -f detection_system.log
```

### Ver estatísticas

As estatísticas aparecem automaticamente a cada ciclo:

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

### Ver temperatura do CPU

```bash
watch -n 2 vcgencmd measure_temp
```

## 🚨 Problemas Comuns

### ❌ "Câmera não encontrada"

```bash
# Listar câmeras disponíveis
v4l2-ctl --list-devices

# Mudar index no config_rpi.json
"camera": {
  "index": 1  // Tente 0, 1, 2...
}
```

### ❌ "GPS sem fix"

```bash
# Verifique se gpsd está rodando
sudo systemctl status gpsd

# Use modo mock para testes
"gps": {
  "backend": "mock"
}
```

### ❌ "Sem conexão com API"

```bash
# Teste a URL manualmente
curl https://sua-api.com/api/detections

# Verifique a fila offline
ls -lh queue/

# A fila tentará enviar automaticamente quando conectar
```

### ❌ "ImportError: No module named 'cv2'"

```bash
# Reinstale OpenCV
pip3 install opencv-python-headless

# Ou use a versão do sistema (mais rápido)
sudo apt-get install python3-opencv
```

### ❌ CPU muito quente (>80°C)

```bash
# Reduza a carga
nano config_rpi.json

# Aumente o intervalo
"capture_interval": 10.0

# Reduza a resolução
"detector": {
  "resize_width": 480
}
```

## 🎛️ Opções de Linha de Comando

```bash
# Modo contínuo (padrão)
python3 src/rpi/main_rpi.py --mode continuous

# Imagem única
python3 src/rpi/main_rpi.py --mode single --image foto.jpg

# Config customizado
python3 src/rpi/main_rpi.py --config meu_config.json

# Combinações
python3 src/rpi/main_rpi.py \
  --config production.json \
  --mode continuous
```

## 🔄 Auto-Start no Boot

```bash
# Durante instalação, escolha "sim" para systemd

# Ou configure manualmente:
sudo cp detection-system.service.example /etc/systemd/system/detection-system.service
sudo nano /etc/systemd/system/detection-system.service  # Edite os caminhos
sudo systemctl daemon-reload
sudo systemctl enable detection-system
sudo systemctl start detection-system

# Ver status
sudo systemctl status detection-system
```

## 📁 Estrutura de Arquivos

```
computacional-vision/
├── config_rpi.json          ← Configure aqui!
├── install_rpi.sh           ← Rode primeiro
├── test_rpi.py              ← Teste depois
├── src/rpi/
│   └── main_rpi.py          ← Script principal
├── captures/                ← Imagens temporárias (auto-deletadas)
├── queue/                   ← Fila offline (persistente)
└── logs/
    └── detection_system.log ← Logs do sistema
```

## 💡 Dicas Pro

### 1. Melhor Performance

```bash
# Limite threads OpenCV
export OPENCV_NUM_THREADS=2

# Execute
python3 src/rpi/main_rpi.py ...
```

### 2. Economizar Espaço

Desabilite imagens anotadas:

```json
{
  "save_annotated": false
}
```

### 3. Debug Detalhado

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### 4. Múltiplas Configurações

```bash
# Produção
python3 src/rpi/main_rpi.py --config config_production.json

# Desenvolvimento
python3 src/rpi/main_rpi.py --config config_dev.json

# Testes
python3 src/rpi/main_rpi.py --config config_test.json
```

### 5. Limpeza Rápida

```bash
# Limpar capturas
rm -rf captures/*

# Limpar fila (CUIDADO!)
rm -rf queue/*

# Limpar logs
rm -rf logs/*
```

## 🆘 Ajuda

**Logs do sistema:**
```bash
tail -f detection_system.log
```

**Logs do serviço:**
```bash
journalctl -u detection-system -f
```

**Status completo:**
```bash
python3 test_rpi.py
```

**Documentação completa:**
```bash
cat README_RPI.md
```

## 📚 Próximos Passos

1. ✅ Instale e configure (você está aqui)
2. 📊 Monitore os logs por alguns minutos
3. 🎯 Ajuste `capture_interval` e `min_confidence`
4. 🚀 Configure auto-start com systemd
5. 🔧 Otimize performance conforme necessário

---

**Pronto para começar?**

```bash
python3 src/rpi/main_rpi.py --config config_rpi.json --mode continuous
```

**Boa sorte! 🍓**