# Arquitetura Técnica do Sistema de Detecção de Mato Alto

> Documento gerado em 2025-09-19 – descreve a arquitetura, fluxos internos, algoritmos e pontos de extensão do projeto.

## 1. Visão Geral

O sistema realiza detecção de áreas com vegetação/mato alto em imagens, vídeos e fluxo de webcam usando uma combinação de:

- Segmentação baseada em cor (HSV + calibração adaptativa)
- Análise de textura (Sobel, Gabor, LBP, variância local)
- Fusão adaptativa (método combinado)
- Pipeline de Deep Learning (U-Net avançada ou simulação reforçada)
- Aprendizado adaptativo incremental (reforça confiança e parâmetros)
- Visualização rica (overlay, bounding boxes estilo dashboard, comparações e painéis analíticos)

Diretórios principais:

```text
src/
  main.py                # Interface principal (menu/CLI)
  capture.py             # Entrada de imagens / vídeo / webcam
  detector.py            # Núcleo de detecção multi-método
  visualizer.py          # Renderização e dashboards
  adaptive_learning.py   # Sistema de aprendizado incremental
  training_system.py     # Processamento de dados de treinamento
models/                  # (Reservado a modelos DL)
output/                  # Resultados gerados
training_data/           # Dados rotulados p/ aprendizado adaptativo
examples/                # Scripts de exemplo e testes
```

## 2. Fluxo Alto Nível

1. Entrada (arquivo, pasta, vídeo ou webcam) via `ImageCapture`
2. Seleção e execução do método de detecção em `GrassDetector`
3. Pós-processamento (limpeza, morfologia, separação, refinamento)
4. Cálculo de métricas e confiança
5. Visualização e exportação (`ResultVisualizer`)
6. (Opcional) Aprendizado incremental (`AdaptiveLearningSystem`)

Representação textual:

```text
[Input] -> capture.ImageCapture -> detector.GrassDetector
    -> (Pré-processamentos condicionais)
    -> Métodos (cor | textura | combinado | deep learning)
    -> Fusão / Pós-processamento
    -> Estatísticas + Confiança + Densidade
    -> visualizer.ResultVisualizer (painel / overlay / boxes)
    -> (Feedback) adaptive_learning.AdaptiveLearningSystem
```

## 3. Componentes Principais

| Componente   | Responsabilidade                                                | Arquivo                |
| ------------ | --------------------------------------------------------------- | ---------------------- |
| Interface    | Menu interativo + CLI, orquestra chamadas                       | `main.py`              |
| Captura      | Carrega imagens, percorre pasta, extrai frames de vídeo, webcam | `capture.py`           |
| Detector     | Implementa todos os métodos de segmentação / análise            | `detector.py`          |
| Visualização | Geração de overlays, bounding boxes, dashboards, comparações    | `visualizer.py`        |
| Aprendizado  | Guarda exemplos, ajusta parâmetros adaptativos                  | `adaptive_learning.py` |
| Treinamento  | Processa lote de dados rotulados e vídeos                       | `training_system.py`   |

## 4. Métodos de Detecção

### 4.1 Baseado em Cor (`detect_grass_color_based`)

Passos:

- Conversão BGR → HSV
- Faixas múltiplas (verde claro, verde escuro, verde amarelado, marrom seco)
- Calibração adaptativa (brilho/contraste) ajusta intervalos
- CLAHE opcional em baixo contraste
- Combinação de máscaras + morfologia (OPEN → CLOSE → CLOSE)
- Remoção de componentes pequenos com área mínima adaptativa
- Estatísticas: cobertura, nº de componentes, pixels detectados
- Score de confiança: consistência de áreas + densidade + foco

### 4.2 Baseado em Textura (`detect_grass_texture_based`)

Recursos:

- Gradientes: Sobel (obrigatório)
- Filtros Gabor (desativáveis em tempo real)
- Local Binary Pattern (LBP) (desativável)
- Variância local / diferença para versão suavizada
- Normalização e fusão ponderada dinâmica (ajuste de pesos se recursos foram pulados)
- Threshold adaptativo (Otsu em modo precisão, fixo em tempo real)
- Morfologia (completa vs rápida)
- Remoção de componentes pequenos

### 4.3 Combinado (`detect_grass_combined`)

Integra:

- Cor + Textura obligatoriamente
- Em modo alta precisão adiciona gradiente direcional e padrões estatísticos (HSV/LAB)
- Pesos adaptativos calculados via confiança × cobertura
- Fusão ponderada + pós-processamento (iterativo + watershed + refinamento de borda)
- Estatísticas avançadas: consenso entre métodos, distribuição espacial, cores dominantes (KMeans)

### 4.4 Deep Learning (`detect_grass_deep_learning`)

- U-Net avançada (encoder/decoder com skip connections) ou simulação heurística
- Multi-escala opcional (0.75 / 1.0 / 1.25) em modo precisão
- Adição potencial de canal de textura
- Ensemble de escalas com pesos pela confiança
- Extração de features analíticas (HSV, LAB, índices espectrais simulados, textura, contexto)
- Máscara final após threshold percentil adaptativo (p50 / p75 / p85)
- Limpeza: morfologia, remoção de ruído, validação por confiança
- Confiança combinada: certeza de predição + consenso com métodos tradicionais + boost adaptativo

## 5. Modos de Execução

| Modo          | Chave                      | Efeito                                                                                    |
| ------------- | -------------------------- | ----------------------------------------------------------------------------------------- |
| Tempo real    | `realtime_params.enabled`  | Reduz resolução, pula Gabor/LBP, frame skip, morfologia simples, confiança simplificada   |
| Alta precisão | `precision_params.enabled` | Multi-escala, Gabor/estatísticas extra, watershed, refino de borda, análise espacial rica |
| Adaptativo    | Selecionado no menu        | Ajusta automaticamente com base no método escolhido                                       |

Troca dinâmica: tecla `M` na execução de webcam.

## 6. Pré e Pós-Processamento

Pré-processamento (precisão): CLAHE, bilateral, sharpening leve.
Pré-processamento (tempo real): downscale (fator 0.5), possível frame skipping.

Pós-processamento:

- Morfologia (OPEN/CLOSE repetida ou simplificada)
- Watershed para regiões densas (>80% cobertura) em modo precisão
- Remoção de pequenas regiões por área mínima ajustável
- Refinamento de bordas com teste de cor adicional

## 7. Métricas e Estatísticas

Principais campos em `stats` (exemplo combinado):

```jsonc
{
  method, grass_pixels, total_pixels, coverage_percentage,
  confidence_score,
  methods_agreement: { coverage_std, confidence_mean, coverage_consistency },
  spatial_analysis: { regions_count, avg_region_size, largest_region_ratio, fragmentation_index },
  component_stats: { color: {...}, texture: {...}, additional: [...] },
  dominant_colors: [(B,G,R), ...],
  mode: 'standard' | 'high_precision'
}
```

`density_analysis`:

```jsonc
{
  num_regions, largest_area, average_area, total_area, coverage_ratio,
  density_classification, area_distribution: { min, max, std }
}
```

Confiança (multi-fatores):

- Consistência de áreas (desvio/ média)
- Densidade (penaliza <5% ou >80%)
- Foco (variância Laplaciano)
- Consenso entre métodos (deep learning × cor × textura)
- Similaridade com padrões aprendidos (boost adaptativo)

## 8. Aprendizado Adaptativo (`AdaptiveLearningSystem`)

Armazena em `knowledge_base.json`:

- Padrões de vegetação e não-vegetação (features HSV/RGB, textura, forma)
- Ajusta parâmetros:
  - `confidence_boost`
  - `vegetation_threshold`
  - `color_sensitivity`
  - `texture_weight`
  - Penalidades de falsos positivos

Pipeline de aprendizado:

1. Extração de features da máscara (região detectada)
2. Armazenamento (limite com pruning, prioridade a exemplos recentes)
3. Ajuste incremental (learning rate ~0.05)
4. Cálculo de similaridade para aumentar ou reduzir confiança futura

## 9. Sistema de Treinamento (`TrainingSystem`)

Funções:

- Pastas: `vegetation/`, `non_vegetation/`, `ambiguous/`, `videos/`
- Processa imagens rotuladas: usa detecção atual como pseudo ground-truth para positivos
- Para negativos: máscara vazia → reforça distinção
- Extrai frames de vídeos (amostragem distribuída)
- Gera relatórios JSON e acumula estatísticas (`training_stats.json`)

Uso típico:

```bash
python src/training_system.py
```

Interativo, mostrando progresso e perguntando se deseja treinar.

## 10. Visualização (`ResultVisualizer`)

Modos:

- Overlay Clássico Melhorado: pintura semitransparente + painel superior/inferior
- Bounding Box / Dashboard: boxes estilizados + cards (cobertura, densidade, regiões, área)
- Painel lateral detalhado (lista ou cards)
- Comparação lado a lado entre métodos
- Mapa de densidade (contornos coloridos + legenda)
- Extra: cores dominantes via KMeans

Heurísticas de estilo: gradientes, sombras, badges de confiança (HIGH / MED / LOW), barras decorativas.

## 11. Estratégias de Performance

- Redução de resolução em tempo real
- Frame skipping durante captura
- Desativação seletiva (Gabor / LBP) em tempo real
- Uso de operações NumPy vetorizadas
- Morfologia simplificada quando possível
- Multi-escala somente sob demanda (alta precisão)

## 12. Tratamento de Cenários Problemáticos

Flags internas (heurísticas):

- `low_light`, `overexposed`
- `low_contrast`
- `method_disagreement` (grandes diferenças cobertura cor × textura)
- `sparse_detection`, `dense_detection`
- `poor_focus`

Essas condições ajustam (ou penalizam) confiança e thresholds.

## 13. Limitações Atuais

- Modelo deep learning pode estar não-treinado (simulação avançada ativa)
- Área estimada em m² é heurística (fator fixo)
- Não há avaliação quantitativa automática (IoU) sem ground truth real
- Conhecimento não é versionado nem segmentado por domínio (ex.: urbano vs rural)
- Falta pipeline de deploy para API externa / container

## 14. Pontos de Extensão

Sugestões de evolução:

1. Integrar pesos reais de U-Net treinada (dataset anotado)
2. Introduzir avaliação quantitativa (IoU, precisão, recall) com conjunto de validação
3. Expor API REST (FastAPI) para uso remoto
4. Adicionar normalização fotométrica (exif → correção de exposição)
5. Geo-suporte (se imagens aéreas com metadados)
6. Otimizar execução com ONNX / TensorRT onde aplicável
7. Persistir histórico de parâmetros adaptativos com rollback
8. Implementar feedback manual (interface de correção de máscara)

## 15. Estruturas de Dados (Resumo)

### `stats` (exemplo)

```jsonc
{
  "method": "combined",
  "grass_pixels": 123456,
  "total_pixels": 921600,
  "coverage_percentage": 13.4,
  "confidence_score": 0.78,
  "methods_agreement": { "coverage_std": 2.1, "confidence_mean": 0.73 },
  "spatial_analysis": { "regions_count": 8, "avg_region_size": 1540.2 },
  "dominant_colors": [
    [34, 170, 60],
    [50, 140, 40]
  ],
  "mode": "standard"
}
```

### `density_analysis`

```jsonc
{
  "num_regions": 8,
  "largest_area": 5400,
  "average_area": 1540.2,
  "total_area": 12321,
  "coverage_ratio": 0.134,
  "density_classification": "medium"
}
```

### Conhecimento Adaptativo (trecho simplificado)

```jsonc
{
  "vegetation_patterns": [
    { "features": { "mean_hsv": [62.1, 80.3, 110.2], "texture_variance": 420.5 }, "timestamp": "..." }
  ],
  "non_vegetation_patterns": [...],
  "parameter_history": [...],
  "version": "1.0"
}
```

## 16. Qualidade e Testes (Sugestões)

Recomendações para reforçar qualidade:

- Testes unitários para: calibração de cor, pós-processamento, cálculo de confiança
- Testes de regressão visual (comparar hashes de imagens resultantes em casos fixos)
- Benchmark (tempo médio por frame nos modos real vs precisão)
- Dataset anotado para validar IoU / métricas clássicas

## 17. Operação & Uso Rápido

### Interativo

```bash
python src/main.py
```

Escolha opções no menu.

### CLI (imagem única)

```bash
python src/main.py --image caminho/arquivo.jpg --method combined
```

### Treinamento adaptativo

```bash
python src/training_system.py
```

## 18. Segurança e Considerações

- Não armazena dados sensíveis
- Processa somente arquivos locais fornecidos
- Requer dependências: OpenCV, NumPy, SciPy, scikit-learn, (opcional) TensorFlow

## 19. Dependências Principais

Presentes em `requirements.txt` (exemplos relevantes):

- opencv-python
- numpy
- scipy
- scikit-learn
- matplotlib
- (opcional) tensorflow

## 20. Resumo Final

O sistema combina heurísticas clássicas (cor + textura) com um arcabouço extensível de deep learning, envolto por um mecanismo de aprendizado incremental leve e visualizações ricas. A arquitetura prioriza modularidade (cada responsabilidade em um módulo), extensibilidade (fácil inserir novos detectores ou camadas de validação) e operação interativa ou automatizada.

---

Se desejar, posso gerar também uma versão resumida, um diagrama gráfico ou scripts de teste automatizados. Basta pedir.
