<script setup>
import { ref, computed } from 'vue'
import { compareMethods, GRASS_METHODS, POTHOLE_METHODS } from '@/services/api'

const file = ref(null)
const preview = ref(null)
const fileInputRef = ref(null)
const dragOver = ref(false)
const detectionType = ref('grass')
const loading = ref(false)
const result = ref(null)
const error = ref(null)

const methodsList = computed(() =>
  detectionType.value === 'grass' ? GRASS_METHODS : POTHOLE_METHODS
)

function onFileChange(e) {
  const f = e.target.files?.[0]
  if (f) setFile(f)
}

function setFile(f) {
  if (!f.type.startsWith('image/')) {
    error.value = 'Por favor, selecione um arquivo de imagem (JPG, PNG, BMP, etc.)'
    return
  }
  file.value = f
  preview.value = URL.createObjectURL(f)
  result.value = null
  error.value = null
}

function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) setFile(f)
}

function onDragOver(e) {
  e.preventDefault()
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function clearFile() {
  file.value = null
  preview.value = null
  result.value = null
  error.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function runComparison() {
  if (!file.value) return

  loading.value = true
  error.value = null
  result.value = null

  try {
    const data = await compareMethods(file.value, {
      detectionType: detectionType.value,
    })
    result.value = data
  } catch (err) {
    error.value = err.message || 'Erro ao comparar métodos'
  } finally {
    loading.value = false
  }
}

function getCoverageColor(pct) {
  if (pct >= 60) return 'text-red-400'
  if (pct >= 30) return 'text-orange-400'
  if (pct >= 10) return 'text-yellow-400'
  return 'text-brand-400'
}

function getCoverageBg(pct) {
  if (pct >= 60) return 'bg-gradient-to-r from-red-500 to-orange-500'
  if (pct >= 30) return 'bg-gradient-to-r from-orange-500 to-yellow-500'
  return 'bg-gradient-to-r from-brand-500 to-emerald-500'
}

function getConfidenceColor(conf) {
  if (conf >= 0.8) return 'text-brand-400'
  if (conf >= 0.6) return 'text-yellow-400'
  return 'text-red-400'
}

function getConfidenceBg(conf) {
  if (conf >= 0.8) return 'bg-gradient-to-r from-brand-500 to-emerald-500'
  if (conf >= 0.6) return 'bg-gradient-to-r from-yellow-500 to-amber-500'
  return 'bg-gradient-to-r from-red-500 to-orange-500'
}

function getMethodIcon(methodValue) {
  const found = methodsList.value.find((m) => m.value === methodValue)
  return found?.icon || '🔍'
}

function getMethodLabel(methodValue) {
  const found = methodsList.value.find((m) => m.value === methodValue)
  return found?.label || methodValue
}

function getPotholeConfidenceBadge(level) {
  switch (level?.toLowerCase()) {
    case 'high':
    case 'alta':
      return 'badge-green'
    case 'medium':
    case 'média':
    case 'media':
      return 'badge-yellow'
    case 'low':
    case 'baixa':
      return 'badge-red'
    default:
      return 'badge-surface'
  }
}

const bestGrassMethod = computed(() => {
  if (!result.value?.results || detectionType.value !== 'grass') return null
  const valid = result.value.results.filter((r) => !r.error)
  if (valid.length === 0) return null
  return valid.reduce((best, r) => (r.confidence > best.confidence ? r : best), valid[0])
})

const bestPotholeMethod = computed(() => {
  if (!result.value?.results || detectionType.value !== 'pothole') return null
  const valid = result.value.results.filter((r) => !r.error)
  if (valid.length === 0) return null
  return valid.reduce((best, r) => (r.confidence > best.confidence ? r : best), valid[0])
})

const bestMethod = computed(() => {
  if (detectionType.value === 'grass') return bestGrassMethod.value
  return bestPotholeMethod.value
})

function openInNewTab(base64) {
  const win = window.open()
  if (win) {
    win.document.write(
      `<img src="data:image/jpeg;base64,${base64}" style="max-width:100%;height:auto;" />`
    )
    win.document.title = 'Comparação de Métodos'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Comparar Métodos</h1>
      <p class="text-sm text-surface-400 mt-1">
        Analise uma imagem com todos os métodos de detecção disponíveis e compare os resultados lado a lado.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Upload + Config -->
      <div class="lg:col-span-1 space-y-4">
        <!-- Detection Type Toggle -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🎯 Tipo de Detecção</h3>
          <div class="grid grid-cols-2 gap-2">
            <button
              @click="detectionType = 'grass'; result = null"
              :disabled="loading"
              :class="[
                'px-3 py-3 rounded-xl text-center transition-all duration-200 text-sm',
                'disabled:opacity-40 disabled:pointer-events-none',
                detectionType === 'grass'
                  ? 'bg-brand-600/15 border border-brand-500/30 text-brand-400 font-semibold'
                  : 'border border-surface-700 text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <div class="text-xl mb-1">🌿</div>
              <div>Mato Alto</div>
            </button>
            <button
              @click="detectionType = 'pothole'; result = null"
              :disabled="loading"
              :class="[
                'px-3 py-3 rounded-xl text-center transition-all duration-200 text-sm',
                'disabled:opacity-40 disabled:pointer-events-none',
                detectionType === 'pothole'
                  ? 'bg-orange-600/15 border border-orange-500/30 text-orange-400 font-semibold'
                  : 'border border-surface-700 text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <div class="text-xl mb-1">🕳️</div>
              <div>Buracos</div>
            </button>
          </div>
        </div>

        <!-- Upload Area -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">📷 Imagem</h3>

          <!-- Drop zone -->
          <div
            v-if="!file"
            @drop="onDrop"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            :class="[
              'border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer',
              dragOver
                ? 'border-brand-500 bg-brand-500/5'
                : 'border-surface-600 hover:border-surface-500 hover:bg-surface-800/30',
            ]"
            @click="fileInputRef?.click()"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFileChange"
            />
            <div class="text-4xl mb-3">🔬</div>
            <p class="text-sm font-medium text-surface-300">Arraste uma imagem aqui</p>
            <p class="text-xs text-surface-500 mt-1">ou clique para selecionar</p>
            <p class="text-[11px] text-surface-600 mt-3">JPG, PNG, BMP, TIFF — até 50MB</p>
          </div>

          <!-- Preview -->
          <div v-else class="relative group">
            <img
              :src="preview"
              alt="Preview"
              class="w-full rounded-xl border border-surface-700 object-cover max-h-[250px]"
            />
            <div
              class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl flex items-center justify-center gap-2"
            >
              <button @click="fileInputRef?.click()" class="btn-secondary btn-sm">Trocar</button>
              <button @click="clearFile" class="btn-danger btn-sm">Remover</button>
            </div>
            <input ref="fileInputRef" type="file" accept="image/*" class="hidden" @change="onFileChange" />
            <div class="absolute bottom-2 left-2 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-[11px] text-surface-300">
              {{ file.name }} · {{ (file.size / 1024).toFixed(0) }}KB
            </div>
          </div>
        </div>

        <!-- Methods Info -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🔍 Métodos que serão testados</h3>
          <div class="space-y-2">
            <div
              v-for="m in methodsList.filter(m => m.value !== 'deeplearning')"
              :key="m.value"
              class="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-surface-800/40"
            >
              <span class="text-base shrink-0">{{ m.icon }}</span>
              <div class="min-w-0">
                <p class="text-sm font-medium text-surface-300">{{ m.label }}</p>
                <p class="text-[11px] text-surface-500 leading-snug">{{ m.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Compare Button -->
        <button
          @click="runComparison"
          :disabled="!file || loading"
          :class="[
            'w-full btn-lg',
            file && !loading
              ? 'btn bg-gradient-to-r from-teal-600 to-emerald-600 text-white shadow-lg shadow-teal-600/20 hover:shadow-teal-500/30 hover:from-teal-500 hover:to-emerald-500 focus-visible:ring-teal-500'
              : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
          ]"
        >
          <template v-if="loading">
            <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Comparando métodos...
          </template>
          <template v-else>
            🔬 Comparar Todos os Métodos
          </template>
        </button>
      </div>

      <!-- Right Column: Results -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Empty state -->
        <div
          v-if="!result && !loading && !error"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="text-5xl mb-4">🔬</div>
          <h3 class="text-lg font-semibold text-surface-300">Pronto para Comparar</h3>
          <p class="text-sm text-surface-500 mt-1 max-w-md">
            Selecione uma imagem e clique em "Comparar Todos os Métodos" para ver como cada algoritmo de detecção se comporta na mesma imagem.
          </p>
          <div class="mt-6 grid grid-cols-3 gap-4 max-w-sm w-full">
            <div
              v-for="m in methodsList.filter(m => m.value !== 'deeplearning').slice(0, 3)"
              :key="m.value"
              class="flex flex-col items-center gap-1.5 px-3 py-3 rounded-xl bg-surface-800/30 border border-surface-700/30"
            >
              <span class="text-xl">{{ m.icon }}</span>
              <span class="text-[11px] text-surface-400 font-medium text-center">{{ m.label }}</span>
            </div>
          </div>
        </div>

        <!-- Loading state -->
        <div
          v-else-if="loading"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="relative">
            <div class="w-16 h-16 rounded-full border-4 border-surface-700 border-t-teal-500 animate-spin" />
            <div class="absolute inset-0 flex items-center justify-center text-xl">🔬</div>
          </div>
          <h3 class="text-lg font-semibold text-surface-300 mt-6">Comparando Métodos...</h3>
          <p class="text-sm text-surface-500 mt-1">
            Executando todos os métodos de detecção na mesma imagem.
          </p>
          <p class="text-xs text-surface-500 mt-2">Isso pode levar alguns segundos.</p>
        </div>

        <!-- Error state -->
        <div
          v-else-if="error"
          class="card p-8 flex flex-col items-center justify-center text-center min-h-[300px]"
        >
          <div class="text-4xl mb-3">❌</div>
          <h3 class="text-lg font-semibold text-red-400">Erro na Comparação</h3>
          <p class="text-sm text-surface-400 mt-1 max-w-md">{{ error }}</p>
          <button @click="runComparison" class="btn-secondary btn-sm mt-4" :disabled="!file">
            Tentar novamente
          </button>
        </div>

        <!-- Results -->
        <template v-if="result">
          <!-- Best Method Recommendation -->
          <div
            v-if="bestMethod"
            class="card p-5 glow-green border-brand-500/20 animate-in stagger-1"
          >
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-xl bg-brand-500/15 flex items-center justify-center text-xl shrink-0">
                🏆
              </div>
              <div>
                <h3 class="text-sm font-bold text-white">Método Recomendado</h3>
                <p class="text-sm text-surface-400 mt-0.5">
                  <span class="text-brand-400 font-semibold">{{ getMethodLabel(bestMethod.method) }}</span>
                  com confiança de
                  <span class="text-brand-400 font-semibold">
                    {{ detectionType === 'grass' ? (bestMethod.confidence * 100).toFixed(1) : (bestMethod.confidence * 100).toFixed(0) }}%
                  </span>
                </p>
              </div>
            </div>
          </div>

          <!-- Comparison Table (Grass) -->
          <div
            v-if="detectionType === 'grass' && result.results"
            class="card overflow-hidden animate-in stagger-2"
          >
            <div class="px-5 py-4 border-b border-surface-700/50">
              <h3 class="section-title">📊 Comparação de Resultados</h3>
            </div>

            <div class="divide-y divide-surface-700/30">
              <div
                v-for="(r, idx) in result.results"
                :key="r.method"
                :class="[
                  'px-5 py-4 transition-colors',
                  bestMethod?.method === r.method ? 'bg-brand-500/5' : 'hover:bg-surface-800/30',
                ]"
              >
                <div class="flex items-center gap-4">
                  <!-- Method Info -->
                  <div class="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      :class="[
                        'w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0',
                        bestMethod?.method === r.method
                          ? 'bg-brand-500/15 ring-2 ring-brand-500/30'
                          : 'bg-surface-800/60',
                      ]"
                    >
                      {{ getMethodIcon(r.method) }}
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <p class="text-sm font-semibold text-surface-100">
                          {{ getMethodLabel(r.method) }}
                        </p>
                        <span
                          v-if="bestMethod?.method === r.method"
                          class="badge-green text-[10px]"
                        >
                          🏆 Melhor
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Coverage -->
                  <div class="text-right shrink-0 w-28">
                    <p class="text-xs text-surface-500 mb-1">Cobertura</p>
                    <div class="flex items-center gap-2 justify-end">
                      <div class="progress-bar w-16 h-2">
                        <div
                          :class="['progress-fill', getCoverageBg(r.coverage_percentage)]"
                          :style="{ width: `${Math.min(r.coverage_percentage, 100)}%` }"
                        />
                      </div>
                      <span :class="['text-sm font-bold tabular-nums', getCoverageColor(r.coverage_percentage)]">
                        {{ r.coverage_percentage }}%
                      </span>
                    </div>
                  </div>

                  <!-- Confidence -->
                  <div class="text-right shrink-0 w-28">
                    <p class="text-xs text-surface-500 mb-1">Confiança</p>
                    <div class="flex items-center gap-2 justify-end">
                      <div class="progress-bar w-16 h-2">
                        <div
                          :class="['progress-fill', getConfidenceBg(r.confidence)]"
                          :style="{ width: `${Math.min(r.confidence * 100, 100)}%` }"
                        />
                      </div>
                      <span :class="['text-sm font-bold tabular-nums', getConfidenceColor(r.confidence)]">
                        {{ (r.confidence * 100).toFixed(1) }}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Comparison Table (Pothole) -->
          <div
            v-if="detectionType === 'pothole' && result.results"
            class="card overflow-hidden animate-in stagger-2"
          >
            <div class="px-5 py-4 border-b border-surface-700/50">
              <h3 class="section-title">📊 Comparação de Resultados</h3>
            </div>

            <div class="divide-y divide-surface-700/30">
              <div
                v-for="(r, idx) in result.results"
                :key="r.method"
                :class="[
                  'px-5 py-4 transition-colors',
                  r.error ? 'opacity-50' : '',
                  bestMethod?.method === r.method ? 'bg-orange-500/5' : 'hover:bg-surface-800/30',
                ]"
              >
                <div v-if="r.error" class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-lg shrink-0">
                    {{ getMethodIcon(r.method) }}
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-surface-400">{{ getMethodLabel(r.method) }}</p>
                    <p class="text-xs text-red-400 mt-0.5">Erro ao processar</p>
                  </div>
                </div>

                <div v-else class="flex items-center gap-4">
                  <!-- Method Info -->
                  <div class="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      :class="[
                        'w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0',
                        bestMethod?.method === r.method
                          ? 'bg-orange-500/15 ring-2 ring-orange-500/30'
                          : 'bg-surface-800/60',
                      ]"
                    >
                      {{ getMethodIcon(r.method) }}
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <p class="text-sm font-semibold text-surface-100">
                          {{ getMethodLabel(r.method) }}
                        </p>
                        <span
                          v-if="bestMethod?.method === r.method"
                          class="badge bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/20 text-[10px]"
                        >
                          🏆 Melhor
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Potholes Count -->
                  <div class="text-right shrink-0 w-24">
                    <p class="text-xs text-surface-500 mb-0.5">Buracos</p>
                    <span class="text-sm font-bold text-orange-400 tabular-nums">
                      {{ r.num_potholes }}
                    </span>
                  </div>

                  <!-- Total Area -->
                  <div class="text-right shrink-0 w-28">
                    <p class="text-xs text-surface-500 mb-0.5">Área Total</p>
                    <span class="text-sm font-bold text-surface-200 tabular-nums">
                      {{ r.total_area?.toLocaleString('pt-BR') || 0 }}
                    </span>
                    <span class="text-[10px] text-surface-500 ml-0.5">px</span>
                  </div>

                  <!-- Confidence -->
                  <div class="text-right shrink-0 w-24">
                    <p class="text-xs text-surface-500 mb-0.5">Confiança</p>
                    <div class="flex items-center gap-1.5 justify-end">
                      <span :class="['text-sm font-bold tabular-nums', getConfidenceColor(r.confidence)]">
                        {{ (r.confidence * 100).toFixed(0) }}%
                      </span>
                      <span :class="getPotholeConfidenceBadge(r.confidence_level)" class="text-[10px]">
                        {{ r.confidence_level }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Visual Comparison Image (Grass only) -->
          <div
            v-if="detectionType === 'grass' && result.comparison_image"
            class="card overflow-hidden animate-in stagger-3"
          >
            <div class="flex items-center justify-between px-5 py-3 border-b border-surface-700/50">
              <h3 class="text-sm font-semibold text-surface-200">🖼️ Comparação Visual</h3>
              <div class="flex items-center gap-2">
                <a
                  v-if="result.file"
                  :href="result.file"
                  target="_blank"
                  class="btn-ghost btn-sm text-xs"
                >
                  ⬇️ Baixar
                </a>
              </div>
            </div>

            <div class="p-3 bg-surface-900/40">
              <div class="relative group">
                <img
                  :src="`data:image/jpeg;base64,${result.comparison_image}`"
                  alt="Comparação Visual"
                  class="w-full rounded-lg border border-surface-700/50 cursor-pointer"
                  @click="openInNewTab(result.comparison_image)"
                />
                <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span class="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm text-[11px] text-surface-300">
                    Clique para ampliar
                  </span>
                </div>
              </div>
            </div>

            <div class="px-5 py-3 border-t border-surface-700/50 flex items-center gap-4 text-xs text-surface-500">
              <span>Imagem original + resultado de cada método lado a lado</span>
            </div>
          </div>

          <!-- Summary Insights -->
          <div
            v-if="result.results && result.results.length > 1"
            class="card p-5 animate-in stagger-4"
          >
            <h3 class="text-sm font-semibold text-surface-200 mb-3">💡 Insights</h3>

            <div class="space-y-2.5">
              <!-- Grass insights -->
              <template v-if="detectionType === 'grass'">
                <div
                  v-if="result.results.length > 1"
                  class="flex items-start gap-2.5 text-sm"
                >
                  <span class="text-base shrink-0 mt-0.5">📈</span>
                  <div>
                    <p class="text-surface-300">
                      A diferença de cobertura entre métodos é de
                      <span class="font-bold text-white">
                        {{ (Math.max(...result.results.map(r => r.coverage_percentage)) - Math.min(...result.results.map(r => r.coverage_percentage))).toFixed(1) }}%
                      </span>
                    </p>
                    <p class="text-xs text-surface-500 mt-0.5">
                      Quanto maior a diferença, mais a escolha do método impacta o resultado.
                    </p>
                  </div>
                </div>

                <div class="flex items-start gap-2.5 text-sm">
                  <span class="text-base shrink-0 mt-0.5">🎯</span>
                  <div>
                    <p class="text-surface-300">
                      O método
                      <span class="font-bold text-brand-400">{{ getMethodLabel(bestMethod?.method) }}</span>
                      teve a maior confiança ({{ (bestMethod?.confidence * 100).toFixed(1) }}%), indicando que é o mais confiável para esta imagem.
                    </p>
                  </div>
                </div>

                <div class="flex items-start gap-2.5 text-sm">
                  <span class="text-base shrink-0 mt-0.5">⚡</span>
                  <div>
                    <p class="text-surface-300">
                      O método <span class="font-bold text-surface-100">Combinado</span> geralmente oferece o melhor equilíbrio entre velocidade e precisão para uso geral.
                    </p>
                  </div>
                </div>
              </template>

              <!-- Pothole insights -->
              <template v-if="detectionType === 'pothole'">
                <div
                  v-for="r in result.results.filter(r => !r.error)"
                  :key="r.method"
                  class="flex items-start gap-2.5 text-sm"
                >
                  <span class="text-base shrink-0 mt-0.5">{{ getMethodIcon(r.method) }}</span>
                  <div>
                    <p class="text-surface-300">
                      <span class="font-semibold text-surface-100">{{ getMethodLabel(r.method) }}</span>:
                      {{ r.num_potholes }} {{ r.num_potholes === 1 ? 'buraco' : 'buracos' }} detectados
                      com confiança de <span :class="getConfidenceColor(r.confidence)" class="font-bold">{{ (r.confidence * 100).toFixed(0) }}%</span>
                      (<span :class="getPotholeConfidenceBadge(r.confidence_level)">{{ r.confidence_level }}</span>)
                    </p>
                  </div>
                </div>

                <div
                  v-if="bestPotholeMethod"
                  class="flex items-start gap-2.5 text-sm pt-2 border-t border-surface-700/40"
                >
                  <span class="text-base shrink-0 mt-0.5">💡</span>
                  <p class="text-surface-300">
                    Recomendação: use o método
                    <span class="font-bold text-orange-400">{{ getMethodLabel(bestPotholeMethod.method) }}</span>
                    para esta imagem.
                  </p>
                </div>
              </template>
            </div>
          </div>

          <!-- Run Again -->
          <div class="flex items-center gap-3">
            <button @click="runComparison" class="btn-secondary" :disabled="!file || loading">
              🔄 Comparar Novamente
            </button>
            <button @click="clearFile" class="btn-ghost">
              Trocar Imagem
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
