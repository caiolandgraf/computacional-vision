<script setup>
import { ref, computed } from 'vue'
import { analyzeImage, GRASS_METHODS, VISUAL_MODES } from '@/services/api'

const file = ref(null)
const preview = ref(null)
const method = ref('combined')
const visualMode = ref('bounding_box')
const loading = ref(false)
const result = ref(null)
const error = ref(null)
const dragOver = ref(false)
const resultTab = ref('detailed')

const fileInputRef = ref(null)

const selectedMethod = computed(() =>
  GRASS_METHODS.find((m) => m.value === method.value)
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

async function analyze() {
  if (!file.value) return

  loading.value = true
  error.value = null
  result.value = null

  try {
    const data = await analyzeImage(file.value, {
      method: method.value,
      visualMode: visualMode.value,
    })
    result.value = data
    resultTab.value = 'detailed'
  } catch (err) {
    error.value = err.message || 'Erro ao analisar imagem'
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

function getCoverageBadge(pct) {
  if (pct >= 60) return 'badge-red'
  if (pct >= 30) return 'badge-yellow'
  if (pct >= 10) return 'badge-blue'
  return 'badge-green'
}

function getCoverageLabel(pct) {
  if (pct >= 60) return 'Muito Alto'
  if (pct >= 30) return 'Alto'
  if (pct >= 10) return 'Moderado'
  return 'Baixo'
}

function getConfidenceColor(conf) {
  if (conf >= 0.8) return 'text-brand-400'
  if (conf >= 0.6) return 'text-yellow-400'
  return 'text-red-400'
}

function getDensityBadge(classification) {
  switch (classification) {
    case 'Alta':
      return 'badge-red'
    case 'Média':
      return 'badge-yellow'
    case 'Baixa':
      return 'badge-green'
    default:
      return 'badge-surface'
  }
}

function openInNewTab(base64) {
  const win = window.open()
  if (win) {
    win.document.write(`<img src="data:image/jpeg;base64,${base64}" style="max-width:100%;height:auto;" />`)
    win.document.title = 'Resultado da Análise'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Analisar Imagem</h1>
      <p class="text-sm text-surface-400 mt-1">
        Faça upload de uma foto para detectar áreas com mato alto usando visão computacional.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Upload + Settings -->
      <div class="lg:col-span-1 space-y-4">
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

            <div class="text-4xl mb-3">📁</div>
            <p class="text-sm font-medium text-surface-300">
              Arraste uma imagem aqui
            </p>
            <p class="text-xs text-surface-500 mt-1">
              ou clique para selecionar
            </p>
            <p class="text-[11px] text-surface-600 mt-3">
              JPG, PNG, BMP, TIFF — até 50MB
            </p>
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
              <button @click="fileInputRef?.click()" class="btn-secondary btn-sm">
                Trocar
              </button>
              <button @click="clearFile" class="btn-danger btn-sm">
                Remover
              </button>
            </div>

            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFileChange"
            />

            <div
              class="absolute bottom-2 left-2 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-[11px] text-surface-300"
            >
              {{ file.name }} · {{ (file.size / 1024).toFixed(0) }}KB
            </div>
          </div>
        </div>

        <!-- Detection Method -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🔍 Método de Detecção</h3>

          <div class="space-y-1.5">
            <button
              v-for="m in GRASS_METHODS"
              :key="m.value"
              @click="method = m.value"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                method === m.value
                  ? 'bg-brand-600/15 border border-brand-500/30 text-brand-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <span class="text-base shrink-0">{{ m.icon }}</span>
              <div class="min-w-0">
                <p class="text-sm font-medium">{{ m.label }}</p>
                <p class="text-[11px] text-surface-500 leading-snug mt-0.5">{{ m.description }}</p>
              </div>

              <div
                v-if="method === m.value"
                class="ml-auto w-4 h-4 rounded-full bg-brand-500 flex items-center justify-center shrink-0"
              >
                <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </button>
          </div>
        </div>

        <!-- Visual Mode -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🎨 Modo Visual</h3>

          <select v-model="visualMode" class="select">
            <option v-for="v in VISUAL_MODES" :key="v.value" :value="v.value">
              {{ v.label }}
            </option>
          </select>
          <p class="text-[11px] text-surface-500 mt-2">
            {{ VISUAL_MODES.find(v => v.value === visualMode)?.description }}
          </p>
        </div>

        <!-- Analyze Button -->
        <button
          @click="analyze"
          :disabled="!file || loading"
          :class="[
            'w-full btn-lg',
            file && !loading ? 'btn-primary' : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
          ]"
        >
          <template v-if="loading">
            <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Analisando...
          </template>
          <template v-else>
            🔍 Analisar Imagem
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
          <div class="text-5xl mb-4">🌿</div>
          <h3 class="text-lg font-semibold text-surface-300">Pronto para Analisar</h3>
          <p class="text-sm text-surface-500 mt-1 max-w-sm">
            Selecione uma imagem, escolha o método de detecção e clique em "Analisar Imagem" para começar.
          </p>
        </div>

        <!-- Loading state -->
        <div
          v-else-if="loading"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="relative">
            <div class="w-16 h-16 rounded-full border-4 border-surface-700 border-t-brand-500 animate-spin" />
            <div class="absolute inset-0 flex items-center justify-center text-xl">🌿</div>
          </div>
          <h3 class="text-lg font-semibold text-surface-300 mt-6">Processando...</h3>
          <p class="text-sm text-surface-500 mt-1">
            Analisando imagem com método <span class="text-surface-300 font-medium">{{ selectedMethod?.label }}</span>
          </p>
        </div>

        <!-- Error state -->
        <div
          v-else-if="error"
          class="card p-8 flex flex-col items-center justify-center text-center min-h-[300px]"
        >
          <div class="text-4xl mb-3">❌</div>
          <h3 class="text-lg font-semibold text-red-400">Erro na Análise</h3>
          <p class="text-sm text-surface-400 mt-1 max-w-md">{{ error }}</p>
          <button @click="analyze" class="btn-secondary btn-sm mt-4" :disabled="!file">
            Tentar novamente
          </button>
        </div>

        <!-- Results -->
        <template v-if="result">
          <!-- Stats Cards Row -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="stat-card animate-in stagger-1">
              <span class="stat-label">Cobertura</span>
              <span :class="['stat-value', getCoverageColor(result.stats.coverage_percentage)]">
                {{ result.stats.coverage_percentage }}%
              </span>
              <span :class="getCoverageBadge(result.stats.coverage_percentage)" class="mt-1 self-start">
                {{ getCoverageLabel(result.stats.coverage_percentage) }}
              </span>
            </div>

            <div class="stat-card animate-in stagger-2">
              <span class="stat-label">Confiança</span>
              <span :class="['stat-value', getConfidenceColor(result.stats.confidence)]">
                {{ (result.stats.confidence * 100).toFixed(1) }}%
              </span>
            </div>

            <div class="stat-card animate-in stagger-3">
              <span class="stat-label">Densidade</span>
              <span class="stat-value text-surface-100">{{ result.density.classification }}</span>
              <span :class="getDensityBadge(result.density.classification)" class="mt-1 self-start">
                {{ result.density.num_regions }} regiões
              </span>
            </div>

            <div class="stat-card animate-in stagger-4">
              <span class="stat-label">Pixels Detectados</span>
              <span class="stat-value text-surface-100 text-lg">
                {{ result.stats.grass_pixels.toLocaleString('pt-BR') }}
              </span>
              <span class="text-[11px] text-surface-500 mt-0.5">
                de {{ result.stats.total_pixels.toLocaleString('pt-BR') }}
              </span>
            </div>
          </div>

          <!-- Coverage Bar -->
          <div class="card p-4 animate-in stagger-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-semibold text-surface-400">Barra de Cobertura</span>
              <span :class="['text-xs font-bold', getCoverageColor(result.stats.coverage_percentage)]">
                {{ result.stats.coverage_percentage }}%
              </span>
            </div>
            <div class="progress-bar h-3">
              <div
                :class="[
                  'progress-fill',
                  result.stats.coverage_percentage >= 60
                    ? 'bg-gradient-to-r from-red-500 to-orange-500'
                    : result.stats.coverage_percentage >= 30
                      ? 'bg-gradient-to-r from-orange-500 to-yellow-500'
                      : 'bg-gradient-to-r from-brand-500 to-emerald-500',
                ]"
                :style="{ width: `${Math.min(result.stats.coverage_percentage, 100)}%` }"
              />
            </div>
          </div>

          <!-- Image Result Tabs -->
          <div class="card overflow-hidden animate-in stagger-4">
            <div class="flex border-b border-surface-700/50">
              <button
                @click="resultTab = 'detailed'"
                :class="[
                  'flex-1 px-4 py-3 text-sm font-medium transition-colors relative',
                  resultTab === 'detailed'
                    ? 'text-brand-400'
                    : 'text-surface-400 hover:text-surface-200',
                ]"
              >
                Análise Detalhada
                <div
                  v-if="resultTab === 'detailed'"
                  class="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500"
                />
              </button>
              <button
                @click="resultTab = 'overlay'"
                :class="[
                  'flex-1 px-4 py-3 text-sm font-medium transition-colors relative',
                  resultTab === 'overlay'
                    ? 'text-brand-400'
                    : 'text-surface-400 hover:text-surface-200',
                ]"
              >
                Overlay
                <div
                  v-if="resultTab === 'overlay'"
                  class="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500"
                />
              </button>
              <button
                @click="resultTab = 'original'"
                :class="[
                  'flex-1 px-4 py-3 text-sm font-medium transition-colors relative',
                  resultTab === 'original'
                    ? 'text-brand-400'
                    : 'text-surface-400 hover:text-surface-200',
                ]"
              >
                Original
                <div
                  v-if="resultTab === 'original'"
                  class="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500"
                />
              </button>
            </div>

            <div class="p-3 bg-surface-900/40">
              <div class="relative group">
                <!-- Detailed image -->
                <img
                  v-if="resultTab === 'detailed' && result.images?.detailed"
                  :src="`data:image/jpeg;base64,${result.images.detailed}`"
                  alt="Análise Detalhada"
                  class="w-full rounded-lg border border-surface-700/50 cursor-pointer"
                  @click="openInNewTab(result.images.detailed)"
                />

                <!-- Overlay image -->
                <img
                  v-else-if="resultTab === 'overlay' && result.images?.overlay"
                  :src="`data:image/jpeg;base64,${result.images.overlay}`"
                  alt="Overlay"
                  class="w-full rounded-lg border border-surface-700/50 cursor-pointer"
                  @click="openInNewTab(result.images.overlay)"
                />

                <!-- Original -->
                <img
                  v-else-if="resultTab === 'original' && preview"
                  :src="preview"
                  alt="Original"
                  class="w-full rounded-lg border border-surface-700/50"
                />

                <!-- Open full size hint -->
                <div
                  v-if="resultTab !== 'original'"
                  class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <span class="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm text-[11px] text-surface-300">
                    Clique para ampliar
                  </span>
                </div>
              </div>
            </div>

            <!-- Download links -->
            <div class="flex items-center gap-2 px-4 py-3 border-t border-surface-700/50">
              <a
                v-if="result.files?.overlay"
                :href="result.files.overlay"
                target="_blank"
                class="btn-ghost btn-sm text-xs"
              >
                ⬇️ Baixar Overlay
              </a>
              <a
                v-if="result.files?.detailed"
                :href="result.files.detailed"
                target="_blank"
                class="btn-ghost btn-sm text-xs"
              >
                ⬇️ Baixar Detalhada
              </a>
            </div>
          </div>

          <!-- Additional Details -->
          <div class="card p-5 animate-in stagger-5">
            <h3 class="text-sm font-semibold text-surface-200 mb-3">📋 Detalhes da Análise</h3>

            <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
              <div class="flex justify-between">
                <span class="text-surface-400">Método</span>
                <span class="text-surface-200 font-medium capitalize">{{ result.method }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Modo Visual</span>
                <span class="text-surface-200 font-medium capitalize">
                  {{ VISUAL_MODES.find(v => v.value === visualMode)?.label || visualMode }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Regiões</span>
                <span class="text-surface-200 font-medium">{{ result.density.num_regions }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Área Média</span>
                <span class="text-surface-200 font-medium">{{ result.density.average_area }} px</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Maior Área</span>
                <span class="text-surface-200 font-medium">{{ result.density.largest_area }} px</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Classificação</span>
                <span :class="getDensityBadge(result.density.classification)">
                  {{ result.density.classification }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
