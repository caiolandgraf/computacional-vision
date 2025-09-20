# 📝 Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-01-26

### 🆕 Adicionado
- **README modernizado** com estrutura profissional e badges
- **Script de setup.sh 2.0** com detecção automática de SO e tratamento de erros
- **Sistema de configuração avançada** com arquivo config.example.json
- **Documentação completa** em docs/:
  - INSTALLATION.md - Guia de instalação detalhado
  - BEST_PRACTICES.md - Melhores práticas de uso
- **Compatibilidade com Python 3.13** 
- **scikit-learn 1.7.2** adicionado como dependência
- **Requirements.txt modernizado** com versões flexíveis e compatibilidade
- **Detecção automática de sistema operacional** no setup
- **Validação robusta de dependências** com retry automático
- **Sistema de cores no terminal** para melhor UX
- **Verificação de saúde do sistema** pós-instalação
- **Suporte a múltiplos gerenciadores de pacote** (apt, yum, brew, pacman)

### 🔧 Melhorado
- **Setup automatizado** com tratamento de erros avançado
- **Compatibilidade multiplataforma** (macOS, Linux, WSL, Windows)
- **Detecção inteligente de versão Python** (3.8-3.13)
- **Instalação de dependências** com fallback e retry
- **Estrutura de documentação** organizada e profissional
- **Mensagens de erro** mais informativas e úteis
- **Performance do setup** com instalação paralela quando possível

### 🐛 Corrigido
- **ModuleNotFoundError: No module named 'sklearn'** - scikit-learn adicionado
- **Problemas de compatibilidade com Python 3.13** - versões atualizadas
- **Falhas silenciosas no setup** - tratamento de erros robusto
- **Dependências conflitantes** - versões compatíveis especificadas
- **Setup não funciona em diferentes shells** - compatibilidade melhorada

### ⚠️ Alterado
- **Requirements.txt** completamente reescrito com versões compatíveis
- **Estrutura de projeto** com nova pasta docs/
- **TensorFlow e PyTorch** tornados opcionais (comentados por padrão)
- **Versões mínimas** atualizadas para melhor compatibilidade

### 🗑️ Removido
- **Dependências desnecessárias** (os-sys, pathlib nativo)
- **Versões fixas problemáticas** de TensorFlow
- **Código obsoleto** no setup original

## [1.5.0] - 2024-XX-XX

### 🆕 Adicionado
- Sistema de confiabilidade com scores 0.0-1.0
- Detecção automática de cenários problemáticos
- Calibração automática para condições de iluminação
- Análise de textura avançada (Gabor, LBP)
- Sistema de aprendizado adaptativo
- Interface de menu interativo melhorada

### 🔧 Melhorado
- Algoritmo de cores com múltiplas faixas HSV
- Performance do método combinado
- Visualizações com dashboards informativos
- Sistema de validação cruzada entre métodos

### 🐛 Corrigido
- Problemas com detecção em baixa iluminação
- Falsos positivos em áreas urbanas
- Performance lenta em imagens grandes

## [1.0.0] - 2024-XX-XX

### 🆕 Primeira versão funcional
- Detecção básica por cor (HSV)
- Análise de textura com filtros Sobel
- Método combinado (cor + textura)
- Interface de linha de comando
- Suporte a imagens e vídeos
- Captura via webcam
- Visualização de resultados

---

## 🔄 Processo de Versionamento

Este projeto usa [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Mudanças incompatíveis na API
- **MINOR** (1.X.0): Novas funcionalidades compatíveis
- **PATCH** (1.1.X): Correções de bugs compatíveis

## 📅 Histórico de Releases

| Versão | Data | Principais Mudanças |
|--------|------|-------------------|
| 2.0.0 | 2025-01-26 | Setup modernizado, docs completas, Python 3.13 |
| 1.5.0 | 2024-XX-XX | Sistema de confiabilidade, aprendizado adaptativo |
| 1.0.0 | 2024-XX-XX | Versão inicial funcional |

## 🚧 Próximas Versões

### v2.1.0 (Planejado)
- [ ] Interface web com dashboard
- [ ] API REST para integração
- [ ] Suporte a GPU (CUDA/Metal)
- [ ] Análise temporal de imagens

### v2.2.0 (Futuro)
- [ ] Modelos de deep learning pré-treinados
- [ ] Segmentação por tipos de vegetação
- [ ] App mobile (iOS/Android)
- [ ] Integração com drones

## 📞 Reportar Problemas

Encontrou um bug ou tem uma sugestão?

1. **Bugs**: [Abrir issue](link-para-issues) com detalhes completos
2. **Features**: [Discussão](link-para-discussions) para novas ideias
3. **Documentação**: Contribuições via pull request

## 🏷️ Tags e Releases

- Todas as versões são tagadas no Git
- Releases incluem binários quando aplicável
- Changelog é atualizado a cada release
- Breaking changes são claramente marcados

---

**Mantenha este arquivo atualizado a cada mudança significativa!** 📝