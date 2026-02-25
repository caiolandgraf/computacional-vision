<script setup>
import { ref, computed } from 'vue'
import { analyzePothole, POTHOLE_METHODS } from '@/services/api'

const file = ref(null)
const preview = ref(null)
const method = ref('combined')
const loading = ref(false)
const result = ref(null)
const error = ref(null)
const dragOver = ref(false)
const fileInputRef = ref(null)

const selectedMethod = computed(() =>
  POTHOLE_METHODS.find((m) => m.value === method.value)
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
    const data = await analyzePothole(file.value, {
      method: method.value,
    })
    result.value = data
  } catch (err) {
    error.value = err.message || 'Erro ao analisar imagem'
  } finally {
    loading.value = false
  }
}

function getConfidenceBadge(level) {
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

function getConfidenceColor(conf) {
  if (conf >= 0.7) return 'text-brand-400'
  if (conf >= 0.4) return 'text-yellow-400'
  return 'text-red-400'
}

function openInNewTab(base64) {
  const win = window.open()
  if (win) {
    win.document.write(`<img src="data:image/jpeg;base64,${base64}" style="max-width:100%;height:auto;" />`)
    win.document.title = 'Detecção de Buracos'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Detectar Buracos</h1>
      <p class="text-sm text-surface-400 mt-1">
        Faça upload de uma foto para identificar buracos no asfalto usando visão computacional.
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
                ? 'border-orange-500 bg-orange-500/5'
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
            <div class="text-4xl mb-3">🕳️</div>
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

        <!-- Detection Method -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🔍 Método de Detecção</h3>
          <div class="space-y-1.5">
            <button
              v-for="m in POTHOLE_METHODS"
              :key="m.value"
              @click="method = m.value"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                method === m.value
                  ? 'bg-orange-600/15 border border-orange-500/30 text-orange-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <span class="text-base shrink-0">{{ m.icon }}</span>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium">{{ m.label }}</p>
                <p class="text-[11px] text-surface-500 leading-snug mt-0.5">{{ m.description }}</p>
              </div>
              <div
                v-if="method === m.value"
                class="w-4 h-4 rounded-full bg-orange-500 flex items-center justify-center shrink-0"
              >
                <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </button>
          </div>
        </div>

        <!-- Analyze Button -->
        <button
          @click="analyze"
          :disabled="!file || loading"
          :class="[
            'w-full btn-lg',
            file && !loading
              ? 'btn bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg shadow-orange-600/20 hover:shadow-orange-500/30 hover:from-orange-500 hover:to-amber-500 focus-visible:ring-orange-500'
              : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
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
            🕳️ Detectar Buracos
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
          <div class="text-5xl mb-4">🕳️</div>
          <h3 class="text-lg font-semibold text-surface-300">Pronto para Detectar</h3>
          <p class="text-sm text-surface-500 mt-1 max-w-sm">
            Selecione uma imagem com asfalto, escolha o método de detecção e clique em "Detectar Buracos".
          </p>
        </div>

        <!-- Loading state -->
        <div
          v-else-if="loading"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="relative">
            <div class="w-16 h-16 rounded-full border-4 border-surface-700 border-t-orange-500 animate-spin" />
            <div class="absolute inset-0 flex items-center justify-center text-xl">🕳️</div>
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
              <span class="stat-label">Buracos Detectados</span>
              <span class="stat-value text-orange-400">{{ result.stats.num_potholes }}</span>
            </div>

            <div class="stat-card animate-in stagger-2">
              <span class="stat-label">Área Total</span>
              <span class="stat-value text-surface-100 text-lg">
                {{ result.stats.total_area.toLocaleString('pt-BR') }}
              </span>
              <span class="text-[11px] text-surface-500">pixels</span>
            </div>

            <div class="stat-card animate-in stagger-3">
              <span class="stat-label">Cobertura</span>
              <span class="stat-value text-amber-400">{{ result.stats.coverage }}%</span>
            </div>

            <div class="stat-card animate-in stagger-4">
              <span class="stat-label">Confiança</span>
              <span :class="['stat-value', getConfidenceColor(result.stats.confidence)]">
                {{ (result.stats.confidence * 100).toFixed(1) }}%
              </span>
              <span :class="getConfidenceBadge(result.stats.confidence_level)" class="mt-1 self-start">
                {{ result.stats.confidence_level }}
              </span>
            </div>
          </div>

          <!-- Flags -->
          <div
            v-if="result.flags && result.flags.length > 0"
            class="card p-4 animate-in stagger-3"
          >
            <div class="flex items-start gap-2.5">
              <span class="text-base">⚠️</span>
              <div>
                <h4 class="text-sm font-semibold text-yellow-400 mb-1">Avisos</h4>
                <ul class="space-y-1">
                  <li
                    v-for="(flag, i) in result.flags"
                    :key="i"
                    class="text-sm text-surface-400"
                  >
                    • {{ flag }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Result Image -->
          <div class="card overflow-hidden animate-in stagger-4">
            <div class="px-4 py-3 border-b border-surface-700/50 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-surface-200">🖼️ Visualização da Detecção</h3>
              <a
                v-if="result.file"
                :href="result.file"
                target="_blank"
                class="btn-ghost btn-sm text-xs"
              >
                ⬇️ Baixar
              </a>
            </div>

            <div class="p-3 bg-surface-900/40">
              <div class="relative group">
                <img
                  v-if="result.image"
                  :src="`data:image/jpeg;base64,${result.image}`"
                  alt="Detecção de Buracos"
                  class="w-full rounded-lg border border-surface-700/50 cursor-pointer"
                  @click="openInNewTab(result.image)"
                />
                <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span class="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm text-[11px] text-surface-300">
                    Clique para ampliar
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Potholes List -->
          <div
            v-if="result.potholes && result.potholes.length > 0"
            class="card p-5 animate-in stagger-5"
          >
            <h3 class="text-sm font-semibold text-surface-200 mb-3">
              🔍 Buracos Detectados ({{ result.potholes.length }})
            </h3>

            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-surface-400 text-xs border-b border-surface-700/50">
                    <th class="pb-2.5 pr-4 font-medium">#</th>
                    <th class="pb-2.5 pr-4 font-medium">Posição</th>
                    <th class="pb-2.5 pr-4 font-medium">Tamanho</th>
                    <th class="pb-2.5 pr-4 font-medium">Área</th>
                    <th class="pb-2.5 font-medium">Confiança</th>
                  </tr>
                </thead>
                <tbody class="text-surface-300">
                  <tr
                    v-for="(p, i) in result.potholes"
                    :key="i"
                    class="border-b border-surface-800/60 last:border-0"
                  >
                    <td class="py-2.5 pr-4 text-surface-500 font-mono text-xs">{{ i + 1 }}</td>
                    <td class="py-2.5 pr-4 font-mono text-xs">
                      ({{ p.bounding_box[0] }}, {{ p.bounding_box[1] }})
                    </td>
                    <td class="py-2.5 pr-4 font-mono text-xs">
                      {{ p.bounding_box[2] }}×{{ p.bounding_box[3] }}
                    </td>
                    <td class="py-2.5 pr-4">
                      {{ p.area.toLocaleString('pt-BR') }} px
                    </td>
                    <td class="py-2.5">
                      <div class="flex items-center gap-2">
                        <div class="progress-bar w-16 h-1.5">
                          <div
                            :class="[
                              'progress-fill',
                              p.confidence_score >= 0.7
                                ? 'bg-brand-500'
                                : p.confidence_score >= 0.4
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500',
                            ]"
                            :style="{ width: `${Math.min(p.confidence_score * 100, 100)}%` }"
                          />
                        </div>
                        <span class="text-xs font-mono">{{ (p.confidence_score * 100).toFixed(0) }}%</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p
              v-if="result.stats.num_potholes > result.potholes.length"
              class="text-xs text-surface-500 mt-3 text-center"
            >
              Mostrando {{ result.potholes.length }} de {{ result.stats.num_potholes }} buracos detectados.
            </p>
          </div>

          <!-- Additional Details -->
          <div class="card p-5 animate-in stagger-6">
            <h3 class="text-sm font-semibold text-surface-200 mb-3">📋 Detalhes da Análise</h3>
            <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
              <div class="flex justify-between">
                <span class="text-surface-400">Método</span>
                <span class="text-surface-200 font-medium capitalize">{{ result.method }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Buracos</span>
                <span class="text-surface-200 font-medium">{{ result.stats.num_potholes }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Área Total</span>
                <span class="text-surface-200 font-medium">{{ result.stats.total_area.toLocaleString('pt-BR') }} px</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Cobertura</span>
                <span class="text-surface-200 font-medium">{{ result.stats.coverage }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Confiança</span>
                <span :class="getConfidenceColor(result.stats.confidence)" class="font-medium">
                  {{ (result.stats.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Nível</span>
                <span :class="getConfidenceBadge(result.stats.confidence_level)">
                  {{ result.stats.confidence_level }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
