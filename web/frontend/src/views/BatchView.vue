<script setup>
import { ref, computed } from 'vue'
import { analyzeBatch, GRASS_METHODS, POTHOLE_METHODS } from '@/services/api'

const files = ref([])
const fileInputRef = ref(null)
const dragOver = ref(false)
const method = ref('combined')
const detectionType = ref('grass')
const loading = ref(false)
const result = ref(null)
const error = ref(null)
const selectedResultIndex = ref(null)

const methodOptions = computed(() =>
  detectionType.value === 'grass' ? GRASS_METHODS : POTHOLE_METHODS
)

const selectedMethodObj = computed(() =>
  methodOptions.value.find((m) => m.value === method.value)
)

function onFileChange(e) {
  const selected = Array.from(e.target.files || [])
  if (selected.length > 0) addFiles(selected)
}

function addFiles(newFiles) {
  const imageFiles = newFiles.filter((f) => f.type.startsWith('image/'))
  if (imageFiles.length === 0) {
    error.value = 'Nenhuma imagem válida selecionada. Use JPG, PNG, BMP, etc.'
    return
  }
  files.value = [...files.value, ...imageFiles]
  error.value = null
  result.value = null
}

function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  const dropped = Array.from(e.dataTransfer?.files || [])
  if (dropped.length > 0) addFiles(dropped)
}

function onDragOver(e) {
  e.preventDefault()
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function removeFile(index) {
  files.value = files.value.filter((_, i) => i !== index)
  if (files.value.length === 0) {
    result.value = null
  }
}

function clearFiles() {
  files.value = []
  result.value = null
  error.value = null
  selectedResultIndex.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function startBatch() {
  if (files.value.length === 0) return

  loading.value = true
  error.value = null
  result.value = null
  selectedResultIndex.value = null

  try {
    const data = await analyzeBatch(files.value, {
      method: method.value,
      detectionType: detectionType.value,
    })
    result.value = data
    if (data.results?.length > 0) {
      selectedResultIndex.value = 0
    }
  } catch (err) {
    error.value = err.message || 'Erro ao processar imagens em lote'
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

function getConfidenceColor(conf) {
  if (conf >= 0.8) return 'text-brand-400'
  if (conf >= 0.6) return 'text-yellow-400'
  return 'text-red-400'
}

function openInNewTab(base64) {
  const win = window.open()
  if (win) {
    win.document.write(
      `<img src="data:image/jpeg;base64,${base64}" style="max-width:100%;height:auto;" />`
    )
    win.document.title = 'Resultado - Análise em Lote'
  }
}

const selectedResult = computed(() => {
  if (selectedResultIndex.value == null || !result.value?.results) return null
  return result.value.results[selectedResultIndex.value]
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Análise em Lote</h1>
      <p class="text-sm text-surface-400 mt-1">
        Envie múltiplas imagens para processá-las de uma vez. Cada imagem será analisada individualmente e os resultados consolidados.
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
              @click="detectionType = 'grass'; method = 'combined'"
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
              @click="detectionType = 'pothole'; method = 'combined'"
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
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-surface-200">📁 Imagens</h3>
            <span v-if="files.length > 0" class="badge-surface">
              {{ files.length }} {{ files.length === 1 ? 'arquivo' : 'arquivos' }}
            </span>
          </div>

          <!-- Drop zone -->
          <div
            @drop="onDrop"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            :class="[
              'border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer',
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
              multiple
              class="hidden"
              @change="onFileChange"
            />
            <div class="text-3xl mb-2">📂</div>
            <p class="text-sm font-medium text-surface-300">
              Arraste imagens aqui
            </p>
            <p class="text-xs text-surface-500 mt-1">ou clique para selecionar múltiplas</p>
            <p class="text-[11px] text-surface-600 mt-2">JPG, PNG, BMP, TIFF</p>
          </div>

          <!-- File List -->
          <div v-if="files.length > 0" class="mt-3 space-y-1 max-h-[200px] overflow-y-auto pr-1">
            <div
              v-for="(f, i) in files"
              :key="i"
              class="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-surface-800/40 group"
            >
              <div class="w-6 h-6 rounded bg-brand-500/10 flex items-center justify-center text-xs shrink-0">🖼️</div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium text-surface-300 truncate">{{ f.name }}</p>
                <p class="text-[10px] text-surface-500">{{ formatFileSize(f.size) }}</p>
              </div>
              <button
                @click="removeFile(i)"
                :disabled="loading"
                class="opacity-0 group-hover:opacity-100 p-1 rounded text-surface-500 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:pointer-events-none"
                title="Remover"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div v-if="files.length > 0" class="mt-3 flex items-center justify-between">
            <button @click="clearFiles" :disabled="loading" class="btn-ghost btn-sm text-xs text-red-400 hover:text-red-300 disabled:opacity-40">
              🗑️ Limpar todos
            </button>
            <button @click="fileInputRef?.click()" :disabled="loading" class="btn-ghost btn-sm text-xs disabled:opacity-40">
              ➕ Adicionar mais
            </button>
          </div>
        </div>

        <!-- Detection Method -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🔍 Método</h3>
          <div class="space-y-1.5">
            <button
              v-for="m in methodOptions"
              :key="m.value"
              @click="method = m.value"
              :disabled="loading"
              :class="[
                'w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                'disabled:opacity-40 disabled:pointer-events-none',
                method === m.value
                  ? detectionType === 'grass'
                    ? 'bg-brand-600/15 border border-brand-500/30 text-brand-400'
                    : 'bg-orange-600/15 border border-orange-500/30 text-orange-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <span class="text-sm shrink-0">{{ m.icon }}</span>
              <div class="min-w-0">
                <p class="text-sm font-medium">{{ m.label }}</p>
                <p class="text-[11px] text-surface-500 leading-snug mt-0.5">{{ m.description }}</p>
              </div>
            </button>
          </div>
        </div>

        <!-- Process Button -->
        <button
          @click="startBatch"
          :disabled="files.length === 0 || loading"
          :class="[
            'w-full btn-lg',
            files.length > 0 && !loading ? 'btn-primary' : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
          ]"
        >
          <template v-if="loading">
            <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processando {{ files.length }} {{ files.length === 1 ? 'imagem' : 'imagens' }}...
          </template>
          <template v-else>
            📁 Processar {{ files.length }} {{ files.length === 1 ? 'imagem' : 'imagens' }}
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
          <div class="text-5xl mb-4">📁</div>
          <h3 class="text-lg font-semibold text-surface-300">Pronto para Análise em Lote</h3>
          <p class="text-sm text-surface-500 mt-1 max-w-md">
            Selecione múltiplas imagens, escolha o tipo e método de detecção, e clique em "Processar" para analisar todas de uma vez.
          </p>
        </div>

        <!-- Loading state -->
        <div
          v-else-if="loading"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="relative">
            <div class="w-16 h-16 rounded-full border-4 border-surface-700 border-t-brand-500 animate-spin" />
            <div class="absolute inset-0 flex items-center justify-center text-xl">📁</div>
          </div>
          <h3 class="text-lg font-semibold text-surface-300 mt-6">Processando em Lote...</h3>
          <p class="text-sm text-surface-500 mt-1">
            Analisando {{ files.length }} {{ files.length === 1 ? 'imagem' : 'imagens' }} com
            <span class="text-surface-300 font-medium">{{ selectedMethodObj?.label }}</span>
          </p>
          <p class="text-xs text-surface-500 mt-3">Isso pode levar alguns minutos para lotes grandes.</p>
        </div>

        <!-- Error -->
        <div
          v-else-if="error"
          class="card p-8 flex flex-col items-center justify-center text-center min-h-[300px]"
        >
          <div class="text-4xl mb-3">❌</div>
          <h3 class="text-lg font-semibold text-red-400">Erro no Processamento</h3>
          <p class="text-sm text-surface-400 mt-1 max-w-md">{{ error }}</p>
          <button @click="startBatch" class="btn-secondary btn-sm mt-4" :disabled="files.length === 0">
            Tentar novamente
          </button>
        </div>

        <!-- Results -->
        <template v-if="result">
          <!-- Summary Stats -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="stat-card animate-in stagger-1">
              <span class="stat-label">Total</span>
              <span class="stat-value text-surface-100">{{ result.summary?.total || 0 }}</span>
              <span class="text-[11px] text-surface-500">imagens</span>
            </div>

            <div class="stat-card animate-in stagger-2">
              <span class="stat-label">Processadas</span>
              <span class="stat-value text-brand-400">{{ result.summary?.processed || 0 }}</span>
              <span class="text-[11px] text-surface-500">com sucesso</span>
            </div>

            <div v-if="result.summary?.avg_coverage != null" class="stat-card animate-in stagger-3">
              <span class="stat-label">Cobertura Média</span>
              <span :class="['stat-value', getCoverageColor(result.summary.avg_coverage)]">
                {{ result.summary.avg_coverage }}%
              </span>
            </div>

            <div v-if="result.summary?.max_coverage != null" class="stat-card animate-in stagger-4">
              <span class="stat-label">Cobertura Máx.</span>
              <span :class="['stat-value', getCoverageColor(result.summary.max_coverage)]">
                {{ result.summary.max_coverage }}%
              </span>
            </div>
          </div>

          <!-- Results Grid: List + Preview -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Results List -->
            <div class="card p-5 animate-in stagger-3">
              <h3 class="text-sm font-semibold text-surface-200 mb-3">
                📋 Resultados ({{ result.results?.length || 0 }})
              </h3>

              <div class="space-y-1.5 max-h-[450px] overflow-y-auto pr-1">
                <button
                  v-for="(r, i) in result.results"
                  :key="i"
                  @click="selectedResultIndex = i"
                  :class="[
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                    selectedResultIndex === i
                      ? 'bg-brand-600/15 border border-brand-500/30'
                      : 'border border-transparent hover:bg-surface-700/40',
                  ]"
                >
                  <div
                    :class="[
                      'w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0',
                      r.error ? 'bg-red-500/10 text-red-400' : 'bg-brand-500/10 text-brand-400',
                    ]"
                  >
                    {{ r.error ? '❌' : '✅' }}
                  </div>

                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-surface-200 truncate">{{ r.filename }}</p>
                    <div class="flex items-center gap-2 mt-0.5">
                      <template v-if="r.error">
                        <span class="text-[11px] text-red-400">{{ r.error }}</span>
                      </template>
                      <template v-else-if="r.coverage != null">
                        <span :class="['text-[11px] font-medium', getCoverageColor(r.coverage)]">
                          {{ r.coverage }}%
                        </span>
                        <span v-if="r.density" class="text-[11px] text-surface-500">· {{ r.density }}</span>
                        <span v-if="r.regions" class="text-[11px] text-surface-500">· {{ r.regions }} regiões</span>
                      </template>
                      <template v-else-if="r.num_potholes != null">
                        <span class="text-[11px] text-orange-400 font-medium">{{ r.num_potholes }} buracos</span>
                        <span class="text-[11px] text-surface-500">· {{ r.confidence }}% conf.</span>
                      </template>
                    </div>
                  </div>

                  <div v-if="r.coverage != null" class="shrink-0">
                    <span :class="getCoverageBadge(r.coverage)" class="text-[10px]">
                      {{ r.coverage }}%
                    </span>
                  </div>
                </button>
              </div>
            </div>

            <!-- Selected Result Preview -->
            <div class="card overflow-hidden animate-in stagger-4">
              <div class="px-4 py-3 border-b border-surface-700/50">
                <h3 class="text-sm font-semibold text-surface-200">
                  {{ selectedResult ? selectedResult.filename : 'Selecione um resultado' }}
                </h3>
              </div>

              <div class="p-3 bg-surface-900/40 min-h-[300px] flex items-center justify-center">
                <template v-if="selectedResult?.image">
                  <div class="relative group w-full">
                    <img
                      :src="`data:image/jpeg;base64,${selectedResult.image}`"
                      alt="Resultado"
                      class="w-full rounded-lg border border-surface-700/50 cursor-pointer"
                      @click="openInNewTab(selectedResult.image)"
                    />
                    <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span class="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-sm text-[11px] text-surface-300">
                        Clique para ampliar
                      </span>
                    </div>
                  </div>
                </template>

                <template v-else-if="selectedResult?.error">
                  <div class="text-center p-6">
                    <div class="text-3xl mb-2">❌</div>
                    <p class="text-sm text-red-400">{{ selectedResult.error }}</p>
                  </div>
                </template>

                <template v-else>
                  <div class="text-center p-6">
                    <div class="text-3xl mb-2 opacity-40">🖼️</div>
                    <p class="text-sm text-surface-500">
                      Selecione um resultado na lista à esquerda para visualizar.
                    </p>
                  </div>
                </template>
              </div>

              <!-- Details -->
              <div v-if="selectedResult && !selectedResult.error" class="px-4 py-3 border-t border-surface-700/50">
                <div class="flex items-center gap-3 flex-wrap text-xs text-surface-500">
                  <span v-if="selectedResult.coverage != null" :class="getCoverageColor(selectedResult.coverage)" class="font-medium">
                    Cobertura: {{ selectedResult.coverage }}%
                  </span>
                  <span v-if="selectedResult.confidence != null" :class="getConfidenceColor(selectedResult.confidence)">
                    Confiança: {{ (selectedResult.confidence * 100).toFixed(1) }}%
                  </span>
                  <span v-if="selectedResult.density">Densidade: {{ selectedResult.density }}</span>
                  <span v-if="selectedResult.regions">{{ selectedResult.regions }} regiões</span>

                  <a
                    v-if="selectedResult.file"
                    :href="selectedResult.file"
                    target="_blank"
                    class="ml-auto text-brand-400 hover:text-brand-300 font-medium"
                  >
                    ⬇️ Baixar
                  </a>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
