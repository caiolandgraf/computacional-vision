<script setup>
import { ref, onMounted, computed } from 'vue'
import { getSettings, updateSettings } from '@/services/api'

const loading = ref(true)
const saving = ref(false)
const error = ref(null)
const successMessage = ref(null)
const settings = ref(null)
const activeTab = ref('texture')

// Editable copies of settings
const textureParams = ref({})
const confidenceParams = ref({})
const realtimeMode = ref(false)

const tabs = [
  { id: 'texture', label: 'Textura', icon: '🧩', description: 'Parâmetros de detecção por textura' },
  { id: 'confidence', label: 'Confiança', icon: '🎯', description: 'Limiares de confiabilidade' },
  { id: 'color', label: 'Cores HSV', icon: '🎨', description: 'Ranges de cor para detecção' },
  { id: 'mode', label: 'Modo', icon: '⚡', description: 'Tempo real vs. alta precisão' },
  { id: 'advanced', label: 'Avançado', icon: '🔧', description: 'Parâmetros avançados do detector' },
]

const textureFields = [
  { key: 'sobel_threshold', label: 'Threshold Sobel', type: 'number', min: 1, max: 255, step: 1, description: 'Limiar para detecção de bordas Sobel. Valores mais altos = menos bordas detectadas.' },
  { key: 'variance_threshold', label: 'Threshold Variância', type: 'number', min: 10, max: 1000, step: 10, description: 'Limiar de variância para classificar textura. Valores mais altos = mais seletivo.' },
  { key: 'min_area', label: 'Área Mínima (px)', type: 'number', min: 100, max: 10000, step: 100, description: 'Área mínima em pixels para considerar como região de mato.' },
  { key: 'lbp_radius', label: 'Raio LBP', type: 'number', min: 1, max: 10, step: 1, description: 'Raio para Local Binary Pattern. Valores maiores capturam texturas maiores.' },
  { key: 'lbp_points', label: 'Pontos LBP', type: 'number', min: 4, max: 48, step: 4, description: 'Número de pontos para LBP. Mais pontos = mais detalhe na textura.' },
  { key: 'morphology_kernel_size', label: 'Kernel Morfologia', type: 'number', min: 3, max: 21, step: 2, description: 'Tamanho do kernel para operações morfológicas. Deve ser ímpar.' },
  { key: 'edge_orientation_bins', label: 'Bins Orientação', type: 'number', min: 4, max: 36, step: 2, description: 'Número de bins para análise de orientação de bordas.' },
]

const confidenceFields = [
  { key: 'min_confidence', label: 'Confiança Mínima', type: 'range', min: 0, max: 1, step: 0.05, description: 'Confiança mínima para aceitar uma detecção. Abaixo disso, o resultado é descartado.' },
  { key: 'consensus_threshold', label: 'Threshold de Consenso', type: 'range', min: 0, max: 1, step: 0.05, description: 'Limiar de consenso entre métodos para considerar detecção válida.' },
  { key: 'outlier_detection', label: 'Detecção de Outliers', type: 'toggle', description: 'Habilita remoção automática de detecções atípicas (outliers).' },
  { key: 'adaptive_threshold', label: 'Threshold Adaptativo', type: 'toggle', description: 'Ajusta automaticamente os limiares baseado no conteúdo da imagem.' },
  { key: 'adaptive_min_area', label: 'Área Mínima Adaptativa', type: 'toggle', description: 'Ajusta automaticamente a área mínima baseado na densidade de detecção.' },
  { key: 'sparse_area_factor', label: 'Fator Área Esparsa', type: 'range', min: 0.1, max: 1.0, step: 0.05, description: 'Fator de redução da área mínima para detecções esparsas.' },
  { key: 'dense_area_factor', label: 'Fator Área Densa', type: 'range', min: 1.0, max: 3.0, step: 0.1, description: 'Fator de aumento da área mínima para detecções densas.' },
]

const colorRangeLabels = {
  green_low: { label: 'Verde (baixo)', color: 'bg-green-500' },
  green_high: { label: 'Verde (alto)', color: 'bg-green-400' },
  brown_low: { label: 'Marrom (baixo)', color: 'bg-amber-700' },
  brown_high: { label: 'Marrom (alto)', color: 'bg-amber-500' },
  yellow_green_low: { label: 'Verde Amarelado (baixo)', color: 'bg-lime-600' },
  yellow_green_high: { label: 'Verde Amarelado (alto)', color: 'bg-lime-400' },
  dark_green_low: { label: 'Verde Escuro (baixo)', color: 'bg-emerald-800' },
  dark_green_high: { label: 'Verde Escuro (alto)', color: 'bg-emerald-600' },
}

const hasChanges = computed(() => {
  if (!settings.value) return false

  // Check texture params
  for (const field of textureFields) {
    if (textureParams.value[field.key] !== settings.value.texture_params?.[field.key]) {
      return true
    }
  }

  // Check confidence params
  for (const field of confidenceFields) {
    if (confidenceParams.value[field.key] !== settings.value.confidence_params?.[field.key]) {
      return true
    }
  }

  // Check realtime mode
  if (realtimeMode.value !== (settings.value.realtime_params?.enabled || false)) {
    return true
  }

  return false
})

async function loadSettings() {
  loading.value = true
  error.value = null
  successMessage.value = null

  try {
    const data = await getSettings()
    settings.value = data

    // Populate editable refs
    textureParams.value = { ...(data.texture_params || {}) }
    confidenceParams.value = { ...(data.confidence_params || {}) }
    realtimeMode.value = data.realtime_params?.enabled || false
  } catch (err) {
    error.value = err.message || 'Erro ao carregar configurações'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  error.value = null
  successMessage.value = null

  try {
    const payload = {
      texture_params: {},
      confidence_params: {},
      realtime_mode: realtimeMode.value,
    }

    // Only send changed texture params
    for (const field of textureFields) {
      if (textureParams.value[field.key] !== settings.value?.texture_params?.[field.key]) {
        payload.texture_params[field.key] = textureParams.value[field.key]
      }
    }

    // Only send changed confidence params
    for (const field of confidenceFields) {
      if (confidenceParams.value[field.key] !== settings.value?.confidence_params?.[field.key]) {
        payload.confidence_params[field.key] = confidenceParams.value[field.key]
      }
    }

    const data = await updateSettings(payload)

    // Update local settings with response
    if (data.settings) {
      settings.value = data.settings
      textureParams.value = { ...(data.settings.texture_params || {}) }
      confidenceParams.value = { ...(data.settings.confidence_params || {}) }
      realtimeMode.value = data.settings.realtime_params?.enabled || false
    }

    successMessage.value = 'Configurações salvas com sucesso!'
    setTimeout(() => {
      successMessage.value = null
    }, 4000)
  } catch (err) {
    error.value = err.message || 'Erro ao salvar configurações'
  } finally {
    saving.value = false
  }
}

function resetToDefaults() {
  if (!settings.value) return

  textureParams.value = { ...(settings.value.texture_params || {}) }
  confidenceParams.value = { ...(settings.value.confidence_params || {}) }
  realtimeMode.value = settings.value.realtime_params?.enabled || false
  successMessage.value = null
  error.value = null
}

function formatRangeValue(value, step) {
  if (step < 1) {
    const decimals = String(step).split('.')[1]?.length || 2
    return Number(value).toFixed(decimals)
  }
  return value
}

function hsvToApproxRgb(h, s, v) {
  // Rough HSV to CSS color for display purposes
  // OpenCV HSV: H=0-180, S=0-255, V=0-255
  const hNorm = (h / 180) * 360
  const sNorm = s / 255
  const vNorm = v / 255
  return `hsl(${hNorm}, ${sNorm * 100}%, ${vNorm * 50}%)`
}

onMounted(loadSettings)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white">Configurações</h1>
        <p class="text-sm text-surface-400 mt-1">
          Ajuste os parâmetros do detector de mato alto e buracos para otimizar os resultados.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="resetToDefaults"
          :disabled="loading || saving || !hasChanges"
          class="btn-ghost btn-sm disabled:opacity-30 disabled:pointer-events-none"
        >
          ↩️ Descartar Alterações
        </button>
        <button
          @click="saveSettings"
          :disabled="loading || saving || !hasChanges"
          :class="[
            'btn-sm',
            hasChanges ? 'btn-primary' : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
          ]"
        >
          <template v-if="saving">
            <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Salvando...
          </template>
          <template v-else>
            💾 Salvar Configurações
          </template>
        </button>
      </div>
    </div>

    <!-- Success Message -->
    <Transition name="slide">
      <div
        v-if="successMessage"
        class="flex items-center gap-3 p-4 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm"
      >
        <span class="text-lg">✅</span>
        <p class="font-medium">{{ successMessage }}</p>
        <button
          @click="successMessage = null"
          class="ml-auto p-1 rounded-lg hover:bg-brand-500/10 text-brand-400"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </Transition>

    <!-- Error Message -->
    <Transition name="slide">
      <div
        v-if="error"
        class="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
      >
        <span class="text-lg">⚠️</span>
        <div class="flex-1">
          <p class="font-semibold">Erro</p>
          <p class="text-red-400/70 text-xs mt-0.5">{{ error }}</p>
        </div>
        <button
          @click="error = null"
          class="p-1 rounded-lg hover:bg-red-500/10 text-red-400"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </Transition>

    <!-- Unsaved Changes Banner -->
    <Transition name="slide">
      <div
        v-if="hasChanges && !loading"
        class="flex items-center gap-3 p-3.5 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm"
      >
        <span class="text-base">📝</span>
        <p class="text-xs font-medium">Você tem alterações não salvas. Clique em "Salvar Configurações" para aplicar.</p>
      </div>
    </Transition>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <div class="card p-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-surface-700/40 animate-pulse" />
          <div class="flex-1 space-y-2">
            <div class="h-5 bg-surface-700/40 rounded w-48 animate-pulse" />
            <div class="h-3 bg-surface-700/40 rounded w-72 animate-pulse" />
          </div>
        </div>
      </div>
      <div class="card p-6 space-y-4">
        <div v-for="n in 5" :key="n" class="h-12 bg-surface-700/40 rounded-xl animate-pulse" />
      </div>
    </div>

    <!-- Settings Content -->
    <div v-else-if="settings" class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Tabs Navigation (Left Column) -->
      <div class="lg:col-span-1 space-y-1.5">
        <div class="card p-2.5 space-y-0.5">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-left transition-all duration-200',
              activeTab === tab.id
                ? 'bg-brand-600/15 text-brand-400 shadow-sm shadow-brand-600/5'
                : 'text-surface-400 hover:text-white hover:bg-surface-800/80',
            ]"
          >
            <span class="text-base shrink-0">{{ tab.icon }}</span>
            <div class="min-w-0">
              <p class="text-sm font-medium">{{ tab.label }}</p>
              <p class="text-[10px] text-surface-500 leading-snug mt-0.5 hidden sm:block">
                {{ tab.description }}
              </p>
            </div>

            <!-- Active indicator -->
            <div
              v-if="activeTab === tab.id"
              class="ml-auto w-1.5 h-1.5 rounded-full bg-brand-500 shrink-0"
            />
          </button>
        </div>

        <!-- Quick Actions -->
        <div class="card p-4 space-y-2.5">
          <h4 class="text-xs font-semibold text-surface-500 uppercase tracking-wider">Ações</h4>
          <button
            @click="loadSettings"
            :disabled="loading || saving"
            class="w-full btn-ghost btn-sm text-xs justify-start disabled:opacity-40"
          >
            🔄 Recarregar do Servidor
          </button>
          <button
            @click="resetToDefaults"
            :disabled="loading || saving || !hasChanges"
            class="w-full btn-ghost btn-sm text-xs justify-start disabled:opacity-40"
          >
            ↩️ Descartar Alterações
          </button>
        </div>
      </div>

      <!-- Tab Content (Right Column) -->
      <div class="lg:col-span-3">
        <!-- Texture Params Tab -->
        <div v-if="activeTab === 'texture'" class="space-y-4">
          <div class="card p-6">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-xl">
                🧩
              </div>
              <div>
                <h2 class="text-lg font-bold text-white">Parâmetros de Textura</h2>
                <p class="text-xs text-surface-400 mt-0.5">
                  Controla como o detector analisa padrões de textura nas imagens.
                </p>
              </div>
            </div>

            <div class="space-y-6">
              <div
                v-for="field in textureFields"
                :key="field.key"
                class="group"
              >
                <div class="flex items-center justify-between mb-2">
                  <div>
                    <label class="text-sm font-medium text-surface-200">
                      {{ field.label }}
                    </label>
                    <p class="text-[11px] text-surface-500 mt-0.5 leading-relaxed max-w-lg">
                      {{ field.description }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2 shrink-0 ml-4">
                    <span
                      v-if="textureParams[field.key] !== settings.texture_params?.[field.key]"
                      class="badge-yellow text-[10px]"
                    >
                      Alterado
                    </span>
                    <span class="text-sm font-mono font-bold text-surface-100 tabular-nums min-w-[60px] text-right">
                      {{ textureParams[field.key] }}
                    </span>
                  </div>
                </div>

                <div class="flex items-center gap-3">
                  <span class="text-[10px] text-surface-500 font-mono w-8 text-right shrink-0">
                    {{ field.min }}
                  </span>
                  <input
                    type="range"
                    v-model.number="textureParams[field.key]"
                    :min="field.min"
                    :max="field.max"
                    :step="field.step"
                    class="flex-1 accent-brand-500 h-2 cursor-pointer"
                  />
                  <span class="text-[10px] text-surface-500 font-mono w-10 shrink-0">
                    {{ field.max }}
                  </span>

                  <input
                    type="number"
                    v-model.number="textureParams[field.key]"
                    :min="field.min"
                    :max="field.max"
                    :step="field.step"
                    class="input w-20 text-center text-sm font-mono shrink-0 py-1.5 px-2"
                  />
                </div>

                <div class="divider" />
              </div>
            </div>
          </div>

          <!-- Gabor Filters Info -->
          <div class="card p-5">
            <h3 class="text-sm font-semibold text-surface-200 mb-3 flex items-center gap-2">
              <span>📐</span>
              Filtros Gabor
            </h3>
            <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
              <div class="flex justify-between">
                <span class="text-surface-400">Ângulos</span>
                <span class="text-surface-200 font-mono text-xs">
                  {{ settings.texture_params?.gabor_angles?.join('°, ') }}°
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Frequências</span>
                <span class="text-surface-200 font-mono text-xs">
                  {{ settings.texture_params?.gabor_frequencies?.join(', ') }}
                </span>
              </div>
            </div>
            <p class="text-[11px] text-surface-500 mt-3">
              Os filtros Gabor são configurados automaticamente. Os ângulos e frequências acima definem como a textura é analisada em diferentes orientações.
            </p>
          </div>
        </div>

        <!-- Confidence Params Tab -->
        <div v-if="activeTab === 'confidence'" class="space-y-4">
          <div class="card p-6">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-xl">
                🎯
              </div>
              <div>
                <h2 class="text-lg font-bold text-white">Parâmetros de Confiança</h2>
                <p class="text-xs text-surface-400 mt-0.5">
                  Ajusta os limiares de confiabilidade e critérios de validação das detecções.
                </p>
              </div>
            </div>

            <div class="space-y-6">
              <div
                v-for="field in confidenceFields"
                :key="field.key"
                class="group"
              >
                <div class="flex items-center justify-between mb-2">
                  <div>
                    <label class="text-sm font-medium text-surface-200">
                      {{ field.label }}
                    </label>
                    <p class="text-[11px] text-surface-500 mt-0.5 leading-relaxed max-w-lg">
                      {{ field.description }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2 shrink-0 ml-4">
                    <span
                      v-if="confidenceParams[field.key] !== settings.confidence_params?.[field.key]"
                      class="badge-yellow text-[10px]"
                    >
                      Alterado
                    </span>
                  </div>
                </div>

                <!-- Toggle Field -->
                <template v-if="field.type === 'toggle'">
                  <div class="flex items-center gap-3">
                    <button
                      @click="confidenceParams[field.key] = !confidenceParams[field.key]"
                      :class="[
                        'relative w-11 h-6 rounded-full transition-colors duration-200 shrink-0',
                        confidenceParams[field.key] ? 'bg-brand-600' : 'bg-surface-600',
                      ]"
                    >
                      <div
                        :class="[
                          'absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200',
                          confidenceParams[field.key] ? 'translate-x-[22px]' : 'translate-x-0.5',
                        ]"
                      />
                    </button>
                    <span class="text-sm text-surface-300">
                      {{ confidenceParams[field.key] ? 'Ativado' : 'Desativado' }}
                    </span>
                  </div>
                </template>

                <!-- Range Field -->
                <template v-else-if="field.type === 'range'">
                  <div class="flex items-center gap-3">
                    <span class="text-[10px] text-surface-500 font-mono w-8 text-right shrink-0">
                      {{ field.min }}
                    </span>
                    <input
                      type="range"
                      v-model.number="confidenceParams[field.key]"
                      :min="field.min"
                      :max="field.max"
                      :step="field.step"
                      class="flex-1 accent-amber-500 h-2 cursor-pointer"
                    />
                    <span class="text-[10px] text-surface-500 font-mono w-8 shrink-0">
                      {{ field.max }}
                    </span>
                    <span class="text-sm font-mono font-bold text-surface-100 tabular-nums min-w-[50px] text-right">
                      {{ formatRangeValue(confidenceParams[field.key], field.step) }}
                    </span>
                  </div>
                </template>

                <div class="divider" />
              </div>
            </div>
          </div>
        </div>

        <!-- Color Ranges Tab -->
        <div v-if="activeTab === 'color'" class="space-y-4">
          <div class="card p-6">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center text-xl">
                🎨
              </div>
              <div>
                <h2 class="text-lg font-bold text-white">Ranges de Cor HSV</h2>
                <p class="text-xs text-surface-400 mt-0.5">
                  Ranges de cor usados na detecção baseada em cores. Formato HSV do OpenCV (H: 0-180, S: 0-255, V: 0-255).
                </p>
              </div>
            </div>

            <div class="space-y-4">
              <div
                v-for="(values, key) in settings.grass_color_ranges"
                :key="key"
                class="flex items-center gap-4 px-4 py-3.5 rounded-xl bg-surface-800/40 border border-surface-700/30"
              >
                <!-- Color indicator -->
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                  <div
                    :class="[
                      'w-8 h-8 rounded-lg shrink-0 border border-surface-600',
                      colorRangeLabels[key]?.color || 'bg-surface-600',
                    ]"
                    :style="Array.isArray(values) && values.length === 3
                      ? { backgroundColor: hsvToApproxRgb(values[0], values[1], values[2]) }
                      : {}"
                  />
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-surface-200">
                      {{ colorRangeLabels[key]?.label || key }}
                    </p>
                    <p class="text-[10px] text-surface-500 font-mono mt-0.5">{{ key }}</p>
                  </div>
                </div>

                <!-- HSV Values -->
                <div class="flex items-center gap-3 shrink-0">
                  <div class="text-center">
                    <p class="text-[10px] text-surface-500 mb-0.5">H</p>
                    <span class="text-sm font-mono font-bold text-surface-100 tabular-nums">
                      {{ Array.isArray(values) ? values[0] : '—' }}
                    </span>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-surface-500 mb-0.5">S</p>
                    <span class="text-sm font-mono font-bold text-surface-100 tabular-nums">
                      {{ Array.isArray(values) ? values[1] : '—' }}
                    </span>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-surface-500 mb-0.5">V</p>
                    <span class="text-sm font-mono font-bold text-surface-100 tabular-nums">
                      {{ Array.isArray(values) ? values[2] : '—' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-blue-500/5 border border-blue-500/10">
              <span class="text-base shrink-0">💡</span>
              <div>
                <p class="text-xs text-blue-300 font-medium">Nota</p>
                <p class="text-[11px] text-surface-400 mt-0.5 leading-relaxed">
                  Os ranges de cor HSV são calibrados automaticamente pelo sistema. Alterações manuais
                  nesses valores estão disponíveis via API direta (<code class="font-mono text-surface-300">PUT /api/settings</code>).
                  A calibração automática ajusta esses valores baseado na iluminação e contraste de cada imagem.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Mode Tab -->
        <div v-if="activeTab === 'mode'" class="space-y-4">
          <div class="card p-6">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-xl">
                ⚡
              </div>
              <div>
                <h2 class="text-lg font-bold text-white">Modo de Operação</h2>
                <p class="text-xs text-surface-400 mt-0.5">
                  Escolha entre modo de tempo real (rápido) e alta precisão (lento, mas mais acurado).
                </p>
              </div>
            </div>

            <!-- Mode Toggle -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <button
                @click="realtimeMode = true"
                :class="[
                  'p-5 rounded-2xl border-2 text-left transition-all duration-300',
                  realtimeMode
                    ? 'border-blue-500/50 bg-blue-500/5 shadow-lg shadow-blue-500/10'
                    : 'border-surface-700 hover:border-surface-600 hover:bg-surface-800/30',
                ]"
              >
                <div class="flex items-center gap-3 mb-3">
                  <div
                    :class="[
                      'w-11 h-11 rounded-xl flex items-center justify-center text-2xl transition-colors',
                      realtimeMode ? 'bg-blue-500/15' : 'bg-surface-800/60',
                    ]"
                  >
                    🚀
                  </div>
                  <div>
                    <h3 :class="['text-sm font-bold', realtimeMode ? 'text-blue-400' : 'text-surface-300']">
                      Tempo Real
                    </h3>
                    <p class="text-[10px] text-surface-500">Rápido, menor precisão</p>
                  </div>
                </div>

                <ul class="space-y-1.5 text-xs text-surface-400">
                  <li class="flex items-center gap-2">
                    <span :class="realtimeMode ? 'text-blue-400' : 'text-surface-600'">✓</span>
                    Pula filtros Gabor pesados
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="realtimeMode ? 'text-blue-400' : 'text-surface-600'">✓</span>
                    Pula LBP complexo
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="realtimeMode ? 'text-blue-400' : 'text-surface-600'">✓</span>
                    Morfologia simplificada
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="realtimeMode ? 'text-blue-400' : 'text-surface-600'">✓</span>
                    Resolução reduzida (50%)
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="realtimeMode ? 'text-blue-400' : 'text-surface-600'">✓</span>
                    Confiança simplificada
                  </li>
                </ul>

                <!-- Selected indicator -->
                <div
                  v-if="realtimeMode"
                  class="mt-4 flex items-center gap-2 text-xs font-semibold text-blue-400"
                >
                  <div class="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center">
                    <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  Selecionado
                </div>
              </button>

              <button
                @click="realtimeMode = false"
                :class="[
                  'p-5 rounded-2xl border-2 text-left transition-all duration-300',
                  !realtimeMode
                    ? 'border-purple-500/50 bg-purple-500/5 shadow-lg shadow-purple-500/10'
                    : 'border-surface-700 hover:border-surface-600 hover:bg-surface-800/30',
                ]"
              >
                <div class="flex items-center gap-3 mb-3">
                  <div
                    :class="[
                      'w-11 h-11 rounded-xl flex items-center justify-center text-2xl transition-colors',
                      !realtimeMode ? 'bg-purple-500/15' : 'bg-surface-800/60',
                    ]"
                  >
                    🎯
                  </div>
                  <div>
                    <h3 :class="['text-sm font-bold', !realtimeMode ? 'text-purple-400' : 'text-surface-300']">
                      Alta Precisão
                    </h3>
                    <p class="text-[10px] text-surface-500">Lento, maior acurácia</p>
                  </div>
                </div>

                <ul class="space-y-1.5 text-xs text-surface-400">
                  <li class="flex items-center gap-2">
                    <span :class="!realtimeMode ? 'text-purple-400' : 'text-surface-600'">✓</span>
                    Análise multi-escala
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="!realtimeMode ? 'text-purple-400' : 'text-surface-600'">✓</span>
                    Filtros Gabor aprimorados
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="!realtimeMode ? 'text-purple-400' : 'text-surface-600'">✓</span>
                    LBP com múltiplos raios
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="!realtimeMode ? 'text-purple-400' : 'text-surface-600'">✓</span>
                    Separação por Watershed
                  </li>
                  <li class="flex items-center gap-2">
                    <span :class="!realtimeMode ? 'text-purple-400' : 'text-surface-600'">✓</span>
                    Refinamento de confiança
                  </li>
                </ul>

                <!-- Selected indicator -->
                <div
                  v-if="!realtimeMode"
                  class="mt-4 flex items-center gap-2 text-xs font-semibold text-purple-400"
                >
                  <div class="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center">
                    <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  Selecionado
                </div>
              </button>
            </div>

            <!-- Current Realtime Params -->
            <div class="card p-5 bg-surface-800/30">
              <h3 class="text-sm font-semibold text-surface-200 mb-3">
                📋 Parâmetros do Modo {{ realtimeMode ? 'Tempo Real' : 'Alta Precisão' }}
              </h3>

              <template v-if="realtimeMode">
                <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
                  <div class="flex justify-between">
                    <span class="text-surface-400">Pular Gabor</span>
                    <span class="text-surface-200 font-medium">{{ settings.realtime_params?.skip_gabor ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Pular LBP</span>
                    <span class="text-surface-200 font-medium">{{ settings.realtime_params?.skip_lbp ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Morfologia Rápida</span>
                    <span class="text-surface-200 font-medium">{{ settings.realtime_params?.fast_morphology ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Resolução Reduzida</span>
                    <span class="text-surface-200 font-medium">{{ (settings.realtime_params?.reduced_resolution || 0.5) * 100 }}%</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Frame Skip</span>
                    <span class="text-surface-200 font-medium">1/{{ settings.realtime_params?.frame_skip || 2 }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Confiança Simpl.</span>
                    <span class="text-surface-200 font-medium">{{ settings.realtime_params?.simple_confidence ? 'Sim' : 'Não' }}</span>
                  </div>
                </div>
              </template>

              <template v-else>
                <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
                  <div class="flex justify-between">
                    <span class="text-surface-400">Multi-escala</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.multi_scale_analysis ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Gabor Aprimorado</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.enhanced_gabor ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">LBP Avançado</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.advanced_lbp ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Análise Gradiente</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.gradient_analysis ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Coerência Textura</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.texture_coherence ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Watershed</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.watershed_separation ? 'Sim' : 'Não' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Iterações Morf.</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.morphology_iterations || 3 }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-400">Refin. Confiança</span>
                    <span class="text-surface-200 font-medium">{{ settings.precision_params?.confidence_refinement ? 'Sim' : 'Não' }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Advanced Tab -->
        <div v-if="activeTab === 'advanced'" class="space-y-4">
          <div class="card p-6">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-xl">
                🔧
              </div>
              <div>
                <h2 class="text-lg font-bold text-white">Configurações Avançadas</h2>
                <p class="text-xs text-surface-400 mt-0.5">
                  Informações de calibração automática e detalhes do sistema.
                </p>
              </div>
            </div>

            <!-- Auto Calibration Info -->
            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-surface-200 flex items-center gap-2">
                <span>🔄</span>
                Calibração Automática
              </h3>

              <div class="grid grid-cols-2 gap-3">
                <div class="px-4 py-3 rounded-xl bg-surface-800/40 border border-surface-700/30">
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-surface-400">Status</span>
                    <span class="badge-green text-[10px]">Ativa</span>
                  </div>
                  <p class="text-xs text-surface-500 mt-1.5">
                    O sistema ajusta automaticamente os ranges de cor e limiares baseado na iluminação e contraste de cada imagem.
                  </p>
                </div>

                <div class="px-4 py-3 rounded-xl bg-surface-800/40 border border-surface-700/30">
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-surface-400">CLAHE</span>
                    <span class="badge-green text-[10px]">Ativo</span>
                  </div>
                  <p class="text-xs text-surface-500 mt-1.5">
                    Contrast Limited Adaptive Histogram Equalization é aplicado automaticamente para imagens com baixo contraste.
                  </p>
                </div>
              </div>

              <div class="divider" />

              <h3 class="text-sm font-semibold text-surface-200 flex items-center gap-2">
                <span>📊</span>
                Sistema
              </h3>

              <div class="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 text-sm">
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">Diretório de Saída</span>
                  <code class="text-xs text-surface-300 font-mono break-all">output/</code>
                </div>
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">Formatos de Imagem</span>
                  <span class="text-xs text-surface-300">.jpg, .png, .bmp, .tiff</span>
                </div>
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">Formatos de Vídeo</span>
                  <span class="text-xs text-surface-300">.mp4, .avi, .mov, .mkv</span>
                </div>
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">Resolução Máxima</span>
                  <span class="text-xs text-surface-300">1920×1080</span>
                </div>
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">Codec de Saída</span>
                  <span class="text-xs text-surface-300 font-mono">mp4v (MPEG-4)</span>
                </div>
                <div>
                  <span class="text-xs text-surface-500 block mb-0.5">API</span>
                  <span class="text-xs text-surface-300">FastAPI + WebSocket</span>
                </div>
              </div>

              <div class="divider" />

              <!-- API Endpoint Reference -->
              <h3 class="text-sm font-semibold text-surface-200 flex items-center gap-2">
                <span>🌐</span>
                Endpoints da API
              </h3>

              <div class="space-y-1.5">
                <div
                  v-for="endpoint in [
                    { method: 'POST', path: '/api/analyze/image', desc: 'Analisar imagem (mato)' },
                    { method: 'POST', path: '/api/analyze/pothole', desc: 'Analisar buracos' },
                    { method: 'POST', path: '/api/analyze/compare', desc: 'Comparar métodos' },
                    { method: 'POST', path: '/api/analyze/batch', desc: 'Análise em lote' },
                    { method: 'POST', path: '/api/video/process', desc: 'Processar vídeo' },
                    { method: 'GET', path: '/api/video/status/:id', desc: 'Status do vídeo' },
                    { method: 'WS', path: '/api/ws/webcam', desc: 'Webcam tempo real' },
                    { method: 'GET', path: '/api/results', desc: 'Listar resultados' },
                    { method: 'GET', path: '/api/settings', desc: 'Configurações' },
                    { method: 'PUT', path: '/api/settings', desc: 'Atualizar configs' },
                  ]"
                  :key="endpoint.path"
                  class="flex items-center gap-3 px-3 py-2 rounded-lg bg-surface-800/30"
                >
                  <span
                    :class="[
                      'text-[10px] font-bold font-mono px-1.5 py-0.5 rounded shrink-0 w-12 text-center',
                      endpoint.method === 'GET' ? 'bg-blue-500/15 text-blue-400' :
                      endpoint.method === 'POST' ? 'bg-brand-500/15 text-brand-400' :
                      endpoint.method === 'PUT' ? 'bg-amber-500/15 text-amber-400' :
                      endpoint.method === 'WS' ? 'bg-purple-500/15 text-purple-400' :
                      'bg-surface-700 text-surface-400'
                    ]"
                  >
                    {{ endpoint.method }}
                  </span>
                  <code class="text-xs text-surface-300 font-mono flex-1">{{ endpoint.path }}</code>
                  <span class="text-[11px] text-surface-500 shrink-0">{{ endpoint.desc }}</span>
                </div>
              </div>

              <div class="mt-4 flex items-start gap-2.5 p-3.5 rounded-xl bg-surface-800/30 border border-surface-700/30">
                <span class="text-base shrink-0">📖</span>
                <div>
                  <p class="text-xs text-surface-300 font-medium">Documentação Interativa</p>
                  <p class="text-[11px] text-surface-500 mt-0.5">
                    Acesse
                    <a
                      href="/docs"
                      target="_blank"
                      class="text-brand-400 hover:text-brand-300 font-medium underline underline-offset-2"
                    >
                      /docs
                    </a>
                    para a documentação Swagger/OpenAPI interativa com todos os endpoints, parâmetros e exemplos.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Floating Save Button (mobile) -->
        <Transition name="slide">
          <div
            v-if="hasChanges && !loading"
            class="lg:hidden fixed bottom-4 left-4 right-4 z-40"
          >
            <button
              @click="saveSettings"
              :disabled="saving"
              class="btn-primary w-full btn-lg shadow-2xl shadow-brand-600/30"
            >
              <template v-if="saving">
                <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Salvando...
              </template>
              <template v-else>
                💾 Salvar Configurações
              </template>
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Error State (no settings loaded) -->
    <div
      v-else-if="!loading && !settings"
      class="card p-12 flex flex-col items-center justify-center text-center"
    >
      <div class="text-5xl mb-4">⚠️</div>
      <h3 class="text-lg font-semibold text-surface-300">Não foi possível carregar as configurações</h3>
      <p class="text-sm text-surface-500 mt-1 max-w-md">
        Verifique se o servidor backend está rodando e tente novamente.
      </p>
      <button @click="loadSettings" class="btn-primary mt-4">
        🔄 Tentar Novamente
      </button>
    </div>
  </div>
</template>
