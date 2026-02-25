<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import {
  processVideo,
  pollVideoJob,
  listVideoJobs,
  GRASS_METHODS,
  VIDEO_VISUAL_MODES,
  VIDEO_QUALITY_MODES,
} from '@/services/api'

const file = ref(null)
const fileInputRef = ref(null)
const dragOver = ref(false)
const method = ref('combined')
const visualMode = ref('1')
const quality = ref('1')
const loading = ref(false)
const error = ref(null)

// Job tracking
const currentJobId = ref(null)
const jobStatus = ref(null)
const jobCompleted = ref(false)
const jobError = ref(null)
let cancelPoll = null

// History
const pastJobs = ref([])
const loadingHistory = ref(false)

const selectedMethod = computed(() =>
  GRASS_METHODS.find((m) => m.value === method.value)
)

const selectedVisual = computed(() =>
  VIDEO_VISUAL_MODES.find((v) => v.value === visualMode.value)
)

const selectedQuality = computed(() =>
  VIDEO_QUALITY_MODES.find((q) => q.value === quality.value)
)

const progressPercent = computed(() => {
  if (!jobStatus.value) return 0
  return jobStatus.value.progress || 0
})

const etaFormatted = computed(() => {
  if (!jobStatus.value?.eta_seconds) return '--'
  const s = jobStatus.value.eta_seconds
  if (s < 60) return `${Math.round(s)}s`
  const m = Math.floor(s / 60)
  const sec = Math.round(s % 60)
  return `${m}m ${sec}s`
})

const isProcessing = computed(
  () => loading.value || (jobStatus.value && !jobCompleted.value && !jobError.value)
)

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function onFileChange(e) {
  const f = e.target.files?.[0]
  if (f) setFile(f)
}

function setFile(f) {
  const validExts = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
  const ext = '.' + f.name.split('.').pop().toLowerCase()
  if (!validExts.includes(ext) && !f.type.startsWith('video/')) {
    error.value = 'Por favor, selecione um arquivo de vídeo (MP4, AVI, MOV, MKV, etc.)'
    return
  }
  file.value = f
  error.value = null
  resetJob()
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
  error.value = null
  resetJob()
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function resetJob() {
  if (cancelPoll) {
    cancelPoll()
    cancelPoll = null
  }
  currentJobId.value = null
  jobStatus.value = null
  jobCompleted.value = false
  jobError.value = null
}

async function startProcessing() {
  if (!file.value) return

  loading.value = true
  error.value = null
  resetJob()

  try {
    const data = await processVideo(file.value, {
      method: method.value,
      visualMode: visualMode.value,
      quality: quality.value,
    })

    currentJobId.value = data.job_id
    loading.value = false

    // Start polling
    cancelPoll = pollVideoJob(data.job_id, {
      interval: 1000,
      onProgress(status) {
        jobStatus.value = status
      },
      onComplete(status) {
        jobStatus.value = status
        jobCompleted.value = true
        loadHistory()
      },
      onError(err) {
        jobError.value = typeof err === 'string' ? err : err?.message || 'Erro desconhecido'
        jobStatus.value = null
      },
    })
  } catch (err) {
    error.value = err.message || 'Erro ao iniciar processamento'
    loading.value = false
  }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const data = await listVideoJobs()
    pastJobs.value = (data.jobs || [])
      .filter((j) => j.id !== currentJobId.value)
      .sort((a, b) => {
        const da = new Date(a.created_at || 0).getTime()
        const db = new Date(b.created_at || 0).getTime()
        return db - da
      })
      .slice(0, 10)
  } catch (_) {
    // silently fail
  } finally {
    loadingHistory.value = false
  }
}

function getStatusBadge(status) {
  switch (status) {
    case 'completed':
      return { cls: 'badge-green', label: 'Concluído', icon: '✅' }
    case 'processing':
      return { cls: 'badge-blue', label: 'Processando', icon: '⚙️' }
    case 'queued':
      return { cls: 'badge-yellow', label: 'Na Fila', icon: '⏳' }
    case 'error':
      return { cls: 'badge-red', label: 'Erro', icon: '❌' }
    default:
      return { cls: 'badge-surface', label: status || '—', icon: '❓' }
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onBeforeUnmount(() => {
  if (cancelPoll) cancelPoll()
})

// Load history on mount
loadHistory()
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Processar Vídeo</h1>
      <p class="text-sm text-surface-400 mt-1">
        Envie um vídeo para gerar uma versão com overlay de detecção — áreas verdes, porcentagens e bounding boxes, igual à webcam.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Upload + Config -->
      <div class="lg:col-span-1 space-y-4">
        <!-- Upload Area -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🎬 Vídeo</h3>

          <!-- Drop zone -->
          <div
            v-if="!file"
            @drop="onDrop"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            :class="[
              'border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer',
              dragOver
                ? 'border-blue-500 bg-blue-500/5'
                : 'border-surface-600 hover:border-surface-500 hover:bg-surface-800/30',
            ]"
            @click="fileInputRef?.click()"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept="video/*,.mp4,.avi,.mov,.mkv,.flv,.wmv"
              class="hidden"
              @change="onFileChange"
            />

            <div class="text-4xl mb-3">🎥</div>
            <p class="text-sm font-medium text-surface-300">Arraste um vídeo aqui</p>
            <p class="text-xs text-surface-500 mt-1">ou clique para selecionar</p>
            <p class="text-[11px] text-surface-600 mt-3">MP4, AVI, MOV, MKV, FLV, WMV</p>
          </div>

          <!-- File selected -->
          <div v-else class="relative">
            <div class="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-surface-800/60 border border-surface-700/50">
              <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-lg shrink-0">
                🎬
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-surface-200 truncate">{{ file.name }}</p>
                <p class="text-[11px] text-surface-500">{{ formatFileSize(file.size) }}</p>
              </div>
              <button
                @click="clearFile"
                :disabled="isProcessing"
                class="p-1.5 rounded-lg text-surface-500 hover:text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-30 disabled:pointer-events-none"
                title="Remover"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              accept="video/*,.mp4,.avi,.mov,.mkv,.flv,.wmv"
              class="hidden"
              @change="onFileChange"
            />
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
              :disabled="isProcessing"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                'disabled:opacity-40 disabled:pointer-events-none',
                method === m.value
                  ? 'bg-brand-600/15 border border-brand-500/30 text-brand-400'
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
                class="w-4 h-4 rounded-full bg-brand-500 flex items-center justify-center shrink-0"
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
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🎨 Modo Visual do Overlay</h3>
          <div class="space-y-1.5">
            <button
              v-for="v in VIDEO_VISUAL_MODES"
              :key="v.value"
              @click="visualMode = v.value"
              :disabled="isProcessing"
              :class="[
                'w-full flex items-start gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200',
                'disabled:opacity-40 disabled:pointer-events-none',
                visualMode === v.value
                  ? 'bg-blue-600/15 border border-blue-500/30 text-blue-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              <div class="min-w-0">
                <p class="text-sm font-medium">{{ v.label }}</p>
                <p class="text-[11px] text-surface-500 leading-snug mt-0.5">{{ v.description }}</p>
              </div>
            </button>
          </div>
        </div>

        <!-- Quality Mode -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">⚡ Qualidade</h3>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="q in VIDEO_QUALITY_MODES"
              :key="q.value"
              @click="quality = q.value"
              :disabled="isProcessing"
              :class="[
                'px-3 py-2.5 rounded-xl text-center transition-all duration-200 text-sm font-medium',
                'disabled:opacity-40 disabled:pointer-events-none',
                quality === q.value
                  ? 'bg-purple-600/15 border border-purple-500/30 text-purple-400'
                  : 'border border-surface-700 text-surface-400 hover:bg-surface-700/40 hover:text-surface-200',
              ]"
            >
              {{ q.label }}
            </button>
          </div>
          <p class="text-[11px] text-surface-500 mt-2">
            {{ selectedQuality?.description }}
          </p>
        </div>

        <!-- Process Button -->
        <button
          @click="startProcessing"
          :disabled="!file || isProcessing"
          :class="[
            'w-full btn-lg',
            file && !isProcessing ? 'btn-primary' : 'btn bg-surface-700 text-surface-500 cursor-not-allowed',
          ]"
        >
          <template v-if="loading">
            <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Enviando...
          </template>
          <template v-else-if="isProcessing">
            <svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processando...
          </template>
          <template v-else>
            🎬 Processar Vídeo
          </template>
        </button>
      </div>

      <!-- Right Column: Progress + Results -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Empty State -->
        <div
          v-if="!currentJobId && !loading && !error && !jobCompleted"
          class="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
        >
          <div class="text-5xl mb-4">🎬</div>
          <h3 class="text-lg font-semibold text-surface-300">Pronto para Processar</h3>
          <p class="text-sm text-surface-500 mt-1 max-w-md">
            Selecione um vídeo, configure o método e modo visual, e clique em "Processar Vídeo".
            Cada frame será analisado e um novo vídeo será gerado com o overlay de detecção.
          </p>
          <div class="mt-6 flex items-center gap-4 text-[11px] text-surface-500">
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-brand-500/30" />
              <span>Áreas detectadas</span>
            </div>
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-blue-500/30" />
              <span>Bounding boxes</span>
            </div>
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-surface-600" />
              <span>% de cobertura</span>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div
          v-if="error"
          class="card p-6 flex items-start gap-3 bg-red-500/5 border-red-500/20"
        >
          <span class="text-xl">❌</span>
          <div>
            <h3 class="font-semibold text-red-400">Erro</h3>
            <p class="text-sm text-surface-400 mt-0.5">{{ error }}</p>
          </div>
        </div>

        <!-- Job Error -->
        <div
          v-if="jobError"
          class="card p-6 flex items-start gap-3 bg-red-500/5 border-red-500/20"
        >
          <span class="text-xl">❌</span>
          <div>
            <h3 class="font-semibold text-red-400">Erro no Processamento</h3>
            <p class="text-sm text-surface-400 mt-0.5">{{ jobError }}</p>
            <button @click="startProcessing" class="btn-secondary btn-sm mt-3" :disabled="!file">
              Tentar novamente
            </button>
          </div>
        </div>

        <!-- Processing Progress -->
        <div
          v-if="jobStatus && !jobCompleted && !jobError"
          class="card p-6 space-y-5"
        >
          <div class="flex items-center justify-between">
            <h3 class="section-title flex items-center gap-2">
              <svg class="w-5 h-5 animate-spin text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processando Vídeo
            </h3>
            <span class="badge-blue">
              {{ jobStatus.status === 'queued' ? 'Na fila' : 'Em progresso' }}
            </span>
          </div>

          <!-- Progress Bar -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-surface-400">Progresso</span>
              <span class="text-sm font-bold text-blue-400">{{ progressPercent.toFixed(1) }}%</span>
            </div>
            <div class="progress-bar h-4 bg-surface-700 rounded-full">
              <div
                class="progress-fill bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                :style="{ width: `${progressPercent}%` }"
              />
            </div>
          </div>

          <!-- Stats Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-surface-800/40 rounded-xl p-3 text-center">
              <p class="text-lg font-bold text-surface-100">
                {{ jobStatus.current_frame || 0 }}
              </p>
              <p class="text-[11px] text-surface-500 mt-0.5">
                de {{ jobStatus.total_frames || '?' }} frames
              </p>
            </div>

            <div class="bg-surface-800/40 rounded-xl p-3 text-center">
              <p class="text-lg font-bold text-blue-400">
                {{ (jobStatus.processing_fps || 0).toFixed(1) }}
              </p>
              <p class="text-[11px] text-surface-500 mt-0.5">FPS</p>
            </div>

            <div class="bg-surface-800/40 rounded-xl p-3 text-center">
              <p class="text-lg font-bold text-brand-400">
                {{ (jobStatus.current_coverage || 0).toFixed(1) }}%
              </p>
              <p class="text-[11px] text-surface-500 mt-0.5">Cobertura Atual</p>
            </div>

            <div class="bg-surface-800/40 rounded-xl p-3 text-center">
              <p class="text-lg font-bold text-purple-400">
                {{ etaFormatted }}
              </p>
              <p class="text-[11px] text-surface-500 mt-0.5">Tempo Restante</p>
            </div>
          </div>

          <!-- Video Info -->
          <div v-if="jobStatus.resolution" class="flex items-center gap-4 flex-wrap text-xs text-surface-500">
            <span>📐 {{ jobStatus.resolution }}</span>
            <span>🎞️ {{ (jobStatus.fps || 0).toFixed(0) }} FPS</span>
            <span>⏱️ {{ (jobStatus.duration || 0).toFixed(1) }}s</span>
            <span>🔍 {{ jobStatus.method || method }}</span>
          </div>
        </div>

        <!-- Completed -->
        <div
          v-if="jobCompleted && jobStatus"
          class="space-y-4"
        >
          <!-- Success Banner -->
          <div class="card p-6 glow-green border-brand-500/20">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 rounded-xl bg-brand-500/15 flex items-center justify-center text-2xl">
                ✅
              </div>
              <div>
                <h3 class="text-lg font-bold text-white">Processamento Concluído!</h3>
                <p class="text-sm text-surface-400">O vídeo foi processado com sucesso.</p>
              </div>
            </div>

            <!-- Download Button -->
            <a
              v-if="jobStatus.output_url"
              :href="jobStatus.output_url"
              target="_blank"
              class="btn-primary btn-lg w-full sm:w-auto inline-flex"
            >
              ⬇️ Baixar Vídeo Processado
            </a>
          </div>

          <!-- Final Stats -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="stat-card animate-in stagger-1">
              <span class="stat-label">Frames</span>
              <span class="stat-value text-surface-100">
                {{ jobStatus.current_frame || 0 }}
              </span>
              <span class="text-[11px] text-surface-500">processados</span>
            </div>

            <div class="stat-card animate-in stagger-2">
              <span class="stat-label">Cobertura Média</span>
              <span class="stat-value text-brand-400">
                {{ (jobStatus.avg_coverage || 0).toFixed(1) }}%
              </span>
            </div>

            <div class="stat-card animate-in stagger-3">
              <span class="stat-label">Cobertura Máx.</span>
              <span class="stat-value text-orange-400">
                {{ (jobStatus.max_coverage || 0).toFixed(1) }}%
              </span>
            </div>

            <div class="stat-card animate-in stagger-4">
              <span class="stat-label">Cobertura Mín.</span>
              <span class="stat-value text-blue-400">
                {{ (jobStatus.min_coverage || 0).toFixed(1) }}%
              </span>
            </div>
          </div>

          <!-- Details -->
          <div class="card p-5 animate-in stagger-5">
            <h3 class="text-sm font-semibold text-surface-200 mb-3">📋 Detalhes do Processamento</h3>
            <div class="grid grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
              <div class="flex justify-between">
                <span class="text-surface-400">Método</span>
                <span class="text-surface-200 font-medium">{{ selectedMethod?.label }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Modo Visual</span>
                <span class="text-surface-200 font-medium">{{ selectedVisual?.label }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Qualidade</span>
                <span class="text-surface-200 font-medium">{{ selectedQuality?.label }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">FPS Processamento</span>
                <span class="text-surface-200 font-medium">{{ (jobStatus.processing_fps || 0).toFixed(1) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Resolução</span>
                <span class="text-surface-200 font-medium">{{ jobStatus.resolution || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Duração</span>
                <span class="text-surface-200 font-medium">{{ (jobStatus.duration || 0).toFixed(1) }}s</span>
              </div>
              <div v-if="jobStatus.completed_at" class="flex justify-between col-span-2">
                <span class="text-surface-400">Concluído em</span>
                <span class="text-surface-200 font-medium">{{ formatDate(jobStatus.completed_at) }}</span>
              </div>
            </div>
          </div>

          <!-- New Video Button -->
          <div class="flex items-center gap-3">
            <button @click="clearFile" class="btn-secondary">
              🎬 Processar Outro Vídeo
            </button>
          </div>
        </div>

        <!-- Past Jobs History -->
        <div v-if="pastJobs.length > 0" class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-4">📜 Histórico de Jobs</h3>

          <div class="space-y-2 max-h-[300px] overflow-y-auto pr-1">
            <div
              v-for="job in pastJobs"
              :key="job.id"
              class="flex items-center gap-3 px-3.5 py-3 rounded-xl bg-surface-800/40 border border-surface-700/30"
            >
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-medium text-surface-200 truncate">
                    {{ job.filename || job.id }}
                  </p>
                  <span :class="getStatusBadge(job.status).cls">
                    {{ getStatusBadge(job.status).label }}
                  </span>
                </div>
                <div class="flex items-center gap-3 mt-1 text-[11px] text-surface-500">
                  <span>{{ formatDate(job.created_at) }}</span>
                  <span v-if="job.avg_coverage != null">Média: {{ job.avg_coverage }}%</span>
                  <span v-if="job.resolution">{{ job.resolution }}</span>
                </div>
              </div>

              <a
                v-if="job.output_url && job.status === 'completed'"
                :href="job.output_url"
                target="_blank"
                class="btn-ghost btn-sm text-xs shrink-0"
                title="Baixar"
              >
                ⬇️
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
