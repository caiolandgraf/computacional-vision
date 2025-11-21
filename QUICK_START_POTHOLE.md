# 🕳️ Guia Rápido - Detecção de Buracos

## ⚡ Início Rápido (5 minutos)

### 1. Teste Rápido

```bash
# Execute o teste automático
python3 quick_test_pothole.py
```

Este script vai:
- ✅ Gerar uma imagem sintética com buracos
- ✅ Testar o sistema de detecção
- ✅ Criar visualização dos resultados em `output/`

### 2. Testar com Sua Própria Imagem

```bash
# Método 1: CLI direto
python3 src/pothole_detector.py sua_imagem.jpg

# Método 2: Menu interativo
python3 src/main.py
# Escolha opção 9, 10 ou 11
```

### 3. Usar no Seu Código Python

```python
from src.pothole_detector import PotholeDetector

# Criar detector
detector = PotholeDetector()

# Analisar imagem
result = detector.detect_image("estrada.jpg", method="combined")

# Ver resultados
print(f"Buracos: {result['num_potholes']}")
print(f"Confiança: {result['confidence']:.2f}")

# Criar visualização
detector.visualize_detections("estrada.jpg", result, "output/resultado.jpg")
```

## 📊 Métodos Disponíveis

| Método | Velocidade | Precisão | Quando Usar |
|--------|------------|----------|-------------|
| `contour` | ⚡⚡⚡ Rápido | ⭐⭐⭐⭐ | Buracos bem definidos |
| `texture` | ⚡⚡ Médio | ⭐⭐⭐ | Bordas gastas |
| `shadow` | ⚡⚡⚡ Rápido | ⭐⭐⭐ | Boa iluminação |
| `combined` | ⚡⚡ Médio | ⭐⭐⭐⭐⭐ | **Recomendado** |

## 🎯 Interpretando os Resultados

### Confiança
- 🟢 **≥ 0.8**: Excelente - Use o resultado diretamente
- 🟡 **0.6-0.79**: Bom - Verifique casos extremos
- 🟠 **0.4-0.59**: Regular - Revisão manual recomendada
- 🔴 **< 0.4**: Baixo - Repita com outro método

### O que o Sistema Retorna

```python
result = {
    'num_potholes': 5,              # Número de buracos detectados
    'total_area': 15420.0,          # Área total em pixels
    'coverage': 3.2,                # Percentual de cobertura
    'confidence': 0.78,             # Score de confiança (0-1)
    'confidence_level': 'MEDIUM',   # Nível: HIGH/MEDIUM/LOW/VERY_LOW
    'flags': [],                    # Alertas (low_light, etc)
    'potholes': [                   # Lista de buracos individuais
        {
            'area': 3084.0,
            'bounding_box': (150, 200, 80, 60),
            'center': (190, 230),
            'confidence_score': 0.82
        },
        # ... mais buracos
    ]
}
```

## ⚙️ Configuração Personalizada

### Detectar Buracos Menores

```python
config = {
    'contour': {
        'min_area': 200,  # Padrão: 500
        'min_circularity': 0.2,  # Padrão: 0.3
    }
}

detector = PotholeDetector(config=config)
result = detector.detect_image("imagem.jpg", method="combined")
```

### Apenas Buracos com Alta Confiança

```python
result = detector.detect_image("imagem.jpg", method="combined")

# Filtrar
high_confidence = [
    p for p in result['potholes'] 
    if p['confidence_score'] >= 0.75
]

print(f"Buracos com alta confiança: {len(high_confidence)}")
```

## 📁 Análise em Lote

```python
from pathlib import Path
from src.pothole_detector import PotholeDetector

detector = PotholeDetector()

# Processar todas as imagens de uma pasta
for img_path in Path("fotos/").glob("*.jpg"):
    result = detector.detect_image(str(img_path), method="combined")
    
    # Salvar visualização
    output = f"output/{img_path.stem}_detected.jpg"
    detector.visualize_detections(str(img_path), result, output)
    
    print(f"{img_path.name}: {result['num_potholes']} buracos")
```

## 🔍 Exemplos de Uso

### 1. Monitoramento de Rodovia

```python
import cv2
from src.pothole_detector import PotholeDetector

detector = PotholeDetector()

# Capturar de câmera
cap = cv2.VideoCapture(0)
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Processar a cada 30 frames
    if frame_count % 30 == 0:
        cv2.imwrite("temp.jpg", frame)
        result = detector.detect_image("temp.jpg", method="contour")
        
        if result['num_potholes'] > 0:
            print(f"⚠️  {result['num_potholes']} buracos detectados!")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
```

### 2. Sistema de Alerta

```python
def analyze_and_alert(image_path):
    detector = PotholeDetector()
    result = detector.detect_image(image_path, method="combined")
    
    # Classificar severidade
    if result['num_potholes'] > 10:
        print("🚨 CRÍTICO: Muitos buracos!")
    elif result['num_potholes'] > 5:
        print("⚠️  ALTO: Atenção necessária")
    elif result['num_potholes'] > 2:
        print("🟡 MÉDIO: Monitorar")
    elif result['num_potholes'] > 0:
        print("🟢 BAIXO: Poucos buracos")
    else:
        print("✅ OK: Nenhum buraco")
    
    return result

# Usar
analyze_and_alert("rodovia_BR101.jpg")
```

### 3. Comparar Métodos

```bash
# Via menu
python3 src/main.py
# Escolha opção 11

# Via script de teste
python3 examples/test_pothole_detection.py
# Escolha opção 3
```

## 🐛 Solução de Problemas

### Problema: Nenhum buraco detectado

**Possíveis causas:**
- Imagem de baixa qualidade
- Sem buracos reais na imagem
- Parâmetros muito rigorosos

**Soluções:**
```python
# Tentar com parâmetros mais sensíveis
config = {
    'contour': {'min_area': 200}
}
detector = PotholeDetector(config=config)

# Ou testar outro método
result = detector.detect_image(img, method="texture")
```

### Problema: Muitos falsos positivos

**Possíveis causas:**
- Manchas de óleo/sujeira
- Textura irregular do asfalto
- Parâmetros muito permissivos

**Soluções:**
```python
# Filtrar por confiança
high_conf = [p for p in result['potholes'] if p['confidence_score'] >= 0.7]

# Ou usar parâmetros mais rigorosos
config = {
    'contour': {
        'min_area': 1000,
        'min_circularity': 0.4
    }
}
```

### Problema: Detecção lenta

**Soluções:**
```python
# Usar método mais rápido
result = detector.detect_image(img, method="contour")

# Redimensionar imagem
img = cv2.imread("large.jpg")
img_small = cv2.resize(img, (640, 480))
cv2.imwrite("small.jpg", img_small)
result = detector.detect_image("small.jpg")
```

## 📚 Documentação Completa

Para informações detalhadas, consulte:
- 📖 `docs/POTHOLE_DETECTION.md` - Documentação completa
- 📖 `DOCUMENTACAO_TECNICA.md` - Documentação técnica do sistema
- 📖 `README.md` - Visão geral do projeto

## 💡 Dicas

1. **Qualidade da Imagem**
   - Use imagens nítidas (sem motion blur)
   - Resolução mínima: 640x480
   - Iluminação adequada é importante

2. **Escolha do Método**
   - Para velocidade: `contour` ou `shadow`
   - Para precisão: `combined`
   - Para testes: compare todos com opção 11

3. **Performance**
   - Imagens grandes são mais lentas
   - Use `contour` para tempo real
   - Processe em lote com múltiplos processos

4. **Confiabilidade**
   - Sempre verifique o score de confiança
   - Use `combined` para análises importantes
   - Considere revisão manual para confiança < 0.7

## 🎯 Casos de Uso Reais

### Manutenção Municipal
```python
# Priorizar buracos por severidade
potholes = result['potholes']
sorted_by_size = sorted(potholes, key=lambda x: x['area'], reverse=True)

print("Buracos priorizados para reparo:")
for i, p in enumerate(sorted_by_size[:5], 1):
    print(f"{i}. Centro: {p['center']}, Área: {p['area']:.0f}px")
```

### Inspeção Automatizada
```python
from pathlib import Path

# Processar múltiplas imagens de inspeção
inspection_dir = Path("inspection_photos/")
results = []

for img in inspection_dir.glob("*.jpg"):
    result = detector.detect_image(str(img), method="combined")
    
    if result['confidence'] >= 0.7 and result['num_potholes'] > 0:
        results.append({
            'image': img.name,
            'potholes': result['num_potholes'],
            'severity': 'HIGH' if result['num_potholes'] > 5 else 'MEDIUM'
        })

# Gerar relatório
print(f"Total de imagens com buracos: {len(results)}")
```

## 🚀 Próximos Passos

1. ✅ Teste com imagens sintéticas: `python3 quick_test_pothole.py`
2. ✅ Teste com suas imagens: `python3 src/pothole_detector.py sua_foto.jpg`
3. ✅ Explore o menu interativo: `python3 src/main.py`
4. ✅ Leia a documentação completa: `docs/POTHOLE_DETECTION.md`
5. ✅ Configure parâmetros para seu caso de uso

---

**Pronto para começar!** 🎉

Execute: `python3 quick_test_pothole.py`
