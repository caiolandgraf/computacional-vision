# 🎓 Sistema de Treinamento para Detecção de Vegetação

Este sistema permite treinar o detector de vegetação com suas próprias imagens e vídeos!

## 📁 Estrutura de Pastas

Coloque seus dados de treinamento nas seguintes pastas:

```
training_data/
├── vegetation/          # ✅ Imagens COM vegetação
├── non_vegetation/      # ❌ Imagens SEM vegetação
├── ambiguous/          # ❓ Casos duvidosos
├── videos/             # 🎬 Vídeos (qualquer categoria)
├── processed_frames/   # 📸 Frames extraídos (automático)
└── validation_results/ # 📊 Relatórios (automático)
```

## 🖼️ Formatos Suportados

### Imagens:

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`

### Vídeos:

- `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`

## 🚀 Como Usar

### 1. Preparar Dados

```bash
# Copie suas imagens para as pastas corretas
cp minhas_plantas/* training_data/vegetation/
cp fotos_urbanas/* training_data/non_vegetation/
cp videos_jardim/* training_data/videos/
```

### 2. Executar Treinamento

```bash
# Ativar ambiente virtual
source venv/bin/activate.fish

# Executar sistema de treinamento
python src/training_system.py
```

### 3. Usar do Código Python

```python
from src.training_system import TrainingSystem

# Inicializar sistema
trainer = TrainingSystem()

# Ver progresso atual
progress = trainer.get_training_progress()
print(f"Imagens disponíveis: {progress['available_data']}")

# Executar treinamento completo
report = trainer.run_full_training()
print(f"Status: {report['status']}")
```

## 📊 O que o Sistema Faz

### 🔍 Processamento de Imagens:

- Analisa cada imagem com o detector atual
- Treina o sistema de aprendizado adaptativo
- Salva exemplos para melhorar a confiança

### 🎬 Processamento de Vídeos:

- Extrai frames automaticamente (máximo 30 por vídeo)
- Salva frames em `processed_frames/unknown/`
- Você pode mover frames para categorias corretas depois

### 🧠 Aprendizado:

- Atualiza base de conhecimento JSON
- Melhora algoritmos de confiança
- Cria padrões para reconhecimento futuro

## 📈 Métricas e Progresso

O sistema rastreia:

- ✅ Total de imagens processadas
- 🌱 Exemplos de vegetação aprendidos
- 🏢 Exemplos de não-vegetação
- 🎬 Vídeos processados
- 🎭 Frames extraídos
- 📊 Sessões de treinamento

## 💡 Dicas Importantes

### ✅ Boas Práticas:

- **Balance os dados**: ~50% vegetação, ~50% não-vegetação
- **Varie as condições**: diferentes iluminações, ângulos, estações
- **Qualidade**: imagens nítidas e bem enquadradas
- **Quantidade**: mínimo 10 exemplos por categoria

### 🎯 Tipos de Imagens Ideais:

**Vegetação:**

- 🌳 Árvores e arbustos
- 🌱 Grama e plantas baixas
- 🌿 Folhagem densa
- 🌾 Campos e jardins

**Não-Vegetação:**

- 🏢 Prédios e construções
- 🛣️ Ruas e calçadas
- 🪨 Rochas e solo nu
- 🏞️ Água e céu

### ⚠️ Evite:

- Imagens muito escuras/borradas
- Fotos com vegetação muito pequena/distante
- Imagens duplicadas
- Vídeos muito longos (>5 minutos)

## 🔄 Fluxo Recomendado

1. **Começar pequeno**: 10-20 imagens por categoria
2. **Testar**: rodar treinamento e ver resultados
3. **Validar**: testar detecção com novas imagens
4. **Expandir**: adicionar mais dados gradualmente
5. **Refinar**: ajustar categorias baseado nos resultados

## 📋 Exemplo de Sessão

```bash
$ python src/training_system.py

🎓 Sistema de Treinamento de Vegetação
==================================================

📊 Estado Atual dos Dados:
  🌱 Imagens de vegetação: 15
  🏢 Imagens sem vegetação: 12
  ❓ Casos ambíguos: 3
  🎬 Vídeos: 2

📈 Estatísticas de Processamento:
  📸 Total processado: 0 imagens
  🎬 Vídeos processados: 0
  🎭 Frames extraídos: 0
  🎯 Sessões de treinamento: 0

💡 Recomendações:
  ✅ Dados balanceados! Execute o treinamento para melhorar o sistema

❓ Executar treinamento com dados disponíveis? (s/n): s

🚀 Iniciando treinamento...
🌱 Processando imagens de vegetação...
🏢 Processando imagens de não-vegetação...
❓ Processando casos ambíguos...
🎬 Processando vídeos...

✅ Treinamento concluído com sucesso!
  📸 Imagens processadas: 30
  🎬 Vídeos processados: 2
  🎭 Frames extraídos: 47

🧠 Sistema de aprendizado atualizado e salvo!
```

## 🎉 Resultado

Após o treinamento, seu sistema de detecção será muito mais preciso e confiante com seus tipos específicos de imagens!

Os dados ficam salvos permanentemente e melhoram a cada sessão de treinamento. 🚀
