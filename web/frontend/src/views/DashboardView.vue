<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { checkHealth, listResults, listVideoJobs } from '@/services/api'
import DetectionChart from '@/components/DetectionChart.vue'
import StatCard from '@/components/StatCard.vue'

const router = useRouter()

const health = ref(null)
const results = ref([])
const videoJobs = ref([])
const loading = ref(true)
const error = ref(null)
const totalImages = ref(0)
const totalVideos = ref(0)
const activeJobs = ref(0)

// ── Chart: File type distribution (Doughnut) ─────────────────
const fileTypeChartLabels = computed(() => {
  const types = {}
  results.value.forEach(r => {
    const ext = r.name?.split('.').pop()?.toLowerCase() || 'outro'
    types[ext] = (types[ext] || 0) + 1
  })
  return Object.keys(types)
})

const fileTypeChartDatasets = computed(() => {
  const types = {}
  results.value.forEach(r => {
    const ext = r.name?.split('.').pop()?.toLowerCase() || 'outro'
    types[ext] = (types[ext] || 0) + 1
  })
  return [
    {
      label: 'Arquivos',
      data: Object.values(types)
    }
  ]
})

// ── Chart: Results timeline (Bar – last 7 days) ──────────────
const timelineChartLabels = computed(() => {
  const labels = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    labels.push(
      d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
    )
  }
  return labels
})

const timelineChartDatasets = computed(() => {
  const imgCounts = new Array(7).fill(0)
  const vidCounts = new Array(7).fill(0)
  const now = new Date()
  const startOfRange = new Date(now)
  startOfRange.setDate(startOfRange.getDate() - 6)
  startOfRange.setHours(0, 0, 0, 0)

  results.value.forEach(r => {
    if (!r.created) return
    const d = new Date(r.created)
    if (d < startOfRange) return
    const diffDays = Math.floor((d - startOfRange) / (1000 * 60 * 60 * 24))
    const idx = Math.min(6, Math.max(0, diffDays))
    if (r.type === 'video') {
      vidCounts[idx]++
    } else {
      imgCounts[idx]++
    }
  })

  return [
    { label: 'Imagens', data: imgCounts, color: 'brand' },
    { label: 'Vídeos', data: vidCounts, color: 'blue' }
  ]
})

// ── Chart: Job status distribution (Doughnut) ────────────────
const jobStatusLabels = computed(() => {
  const statuses = {}
  videoJobs.value.forEach(j => {
    const label =
      j.status === 'completed'
        ? 'Concluído'
        : j.status === 'processing'
          ? 'Processando'
          : j.status === 'queued'
            ? 'Na fila'
            : j.status === 'error'
              ? 'Erro'
              : j.status
    statuses[label] = (statuses[label] || 0) + 1
  })
  return Object.keys(statuses)
})

const jobStatusDatasets = computed(() => {
  const statuses = {}
  videoJobs.value.forEach(j => {
    const label =
      j.status === 'completed'
        ? 'Concluído'
        : j.status === 'processing'
          ? 'Processando'
          : j.status === 'queued'
            ? 'Na fila'
            : j.status === 'error'
              ? 'Erro'
              : j.status
    statuses[label] = (statuses[label] || 0) + 1
  })
  return [
    {
      label: 'Jobs',
      data: Object.values(statuses)
    }
  ]
})

// ── Total storage used ───────────────────────────────────────
const totalStorageFormatted = computed(() => {
  const totalKb = results.value.reduce((sum, r) => sum + (r.size_kb || 0), 0)
  if (totalKb > 1024) return `${(totalKb / 1024).toFixed(1)} MB`
  return `${totalKb.toFixed(0)} KB`
})

const quickActions = [
  {
    title: 'Analisar Imagem',
    description: 'Detectar mato alto em uma foto',
    icon: '🌿',
    route: '/analyze',
    color: 'from-brand-500 to-emerald-600',
    shadow: 'shadow-brand-600/20'
  },
  {
    title: 'Detectar Buracos',
    description: 'Identificar buracos no asfalto',
    icon: '🕳️',
    route: '/pothole',
    color: 'from-orange-500 to-amber-600',
    shadow: 'shadow-orange-600/20'
  },
  {
    title: 'Processar Vídeo',
    description: 'Gerar vídeo com overlay de detecção',
    icon: '🎬',
    route: '/video',
    color: 'from-blue-500 to-cyan-600',
    shadow: 'shadow-blue-600/20'
  },
  {
    title: 'Webcam Tempo Real',
    description: 'Análise ao vivo pela webcam',
    icon: '📹',
    route: '/webcam',
    color: 'from-purple-500 to-violet-600',
    shadow: 'shadow-purple-600/20'
  },
  {
    title: 'Análise em Lote',
    description: 'Processar múltiplas imagens',
    icon: '📁',
    route: '/batch',
    color: 'from-pink-500 to-rose-600',
    shadow: 'shadow-pink-600/20'
  },
  {
    title: 'Comparar Métodos',
    description: 'Testar todos os métodos em uma imagem',
    icon: '🔬',
    route: '/compare',
    color: 'from-teal-500 to-emerald-600',
    shadow: 'shadow-teal-600/20'
  }
]

async function loadData() {
  loading.value = true
  error.value = null

  try {
    const [healthRes, resultsRes, jobsRes] = await Promise.allSettled([
      checkHealth(),
      listResults(100),
      listVideoJobs()
    ])

    if (healthRes.status === 'fulfilled') {
      health.value = healthRes.value
    }

    if (resultsRes.status === 'fulfilled') {
      results.value = resultsRes.value.results || []
      totalImages.value = results.value.filter(r => r.type === 'image').length
      totalVideos.value = results.value.filter(r => r.type === 'video').length
    }

    if (jobsRes.status === 'fulfilled') {
      videoJobs.value = jobsRes.value.jobs || []
      activeJobs.value = videoJobs.value.filter(
        j => j.status === 'processing' || j.status === 'queued'
      ).length
    }
  } catch (err) {
    error.value = err.message || 'Erro ao carregar dados'
  } finally {
    loading.value = false
  }
}

function navigateTo(route_path) {
  router.push(route_path)
}

function formatDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatSize(kb) {
  if (kb > 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(0)} KB`
}

function getJobStatusBadge(status) {
  switch (status) {
    case 'completed':
      return { class: 'badge-green', label: 'Concluído' }
    case 'processing':
      return { class: 'badge-blue', label: 'Processando' }
    case 'queued':
      return { class: 'badge-yellow', label: 'Na fila' }
    case 'error':
      return { class: 'badge-red', label: 'Erro' }
    default:
      return { class: 'badge-surface', label: status }
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6 sm:space-y-8">
    <!-- Hero Header -->
    <div class="relative overflow-hidden card p-6 sm:p-8">
      <div
        class="absolute inset-0 bg-gradient-to-br from-brand-600/10 via-transparent to-emerald-600/5 pointer-events-none"
      />
      <div
        class="absolute top-0 right-0 w-64 h-64 bg-brand-500/5 rounded-full blur-3xl pointer-events-none"
      />

      <div class="relative">
        <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
          <span class="text-gradient">Sistema de Detecção</span>
        </h1>
        <p
          class="mt-2 text-surface-400 text-sm sm:text-base max-w-xl leading-relaxed"
        >
          Visão computacional para identificar áreas com mato alto e buracos em
          imagens, vídeos e webcam em tempo real.
        </p>

        <!-- Connection status -->
        <div class="mt-4 flex items-center gap-3 flex-wrap">
          <div
            v-if="health"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20"
          >
            <div class="w-2 h-2 rounded-full bg-brand-500 animate-pulse-slow" />
            <span class="text-xs font-semibold text-brand-400"
              >Servidor Online</span
            >
          </div>
          <div
            v-else-if="!loading"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20"
          >
            <div class="w-2 h-2 rounded-full bg-red-500" />
            <span class="text-xs font-semibold text-red-400"
              >Servidor Offline</span
            >
          </div>

          <div
            v-if="health?.components?.tensorflow"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20"
          >
            <span class="text-xs font-semibold text-purple-400"
              >🧠 TensorFlow</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- Error banner -->
    <div
      v-if="error"
      class="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
    >
      <span class="text-lg">⚠️</span>
      <div>
        <p class="font-semibold">Erro ao conectar com o servidor</p>
        <p class="text-red-400/70 text-xs mt-0.5">{{ error }}</p>
      </div>
      <button
        @click="loadData"
        class="ml-auto btn-sm btn-ghost text-red-400 hover:text-red-300"
      >
        Tentar novamente
      </button>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
      <StatCard
        class="animate-in stagger-1"
        label="Imagens"
        :value="totalImages"
        icon="🖼️"
        color="brand"
        :loading="loading"
        subtitle="Resultados de análise"
        :clickable="true"
        @click="navigateTo('/results')"
      />
      <StatCard
        class="animate-in stagger-2"
        label="Vídeos"
        :value="totalVideos"
        icon="🎬"
        color="blue"
        :loading="loading"
        subtitle="Vídeos processados"
        :clickable="true"
        @click="navigateTo('/video')"
      />
      <StatCard
        class="animate-in stagger-3"
        label="Jobs Ativos"
        :value="activeJobs"
        icon="⚡"
        color="purple"
        :loading="loading"
        subtitle="Em processamento"
      />
      <StatCard
        class="animate-in stagger-4"
        label="Armazenamento"
        :value="totalStorageFormatted"
        icon="💾"
        color="orange"
        :loading="loading"
        :subtitle="`${results.length} resultado(s) total`"
        :clickable="true"
        @click="navigateTo('/results')"
      />
    </div>

    <!-- Quick Actions Grid -->
    <div>
      <h3 class="section-title mb-4">Ações Rápidas</h3>
      <div
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
      >
        <button
          v-for="(action, idx) in quickActions"
          :key="action.route"
          @click="navigateTo(action.route)"
          :class="[
            'card-hover p-5 text-left group animate-in',
            `stagger-${idx + 1}`
          ]"
        >
          <div class="flex items-start gap-4">
            <div
              :class="[
                'w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center text-xl',
                'shadow-lg transition-transform duration-300 group-hover:scale-110 shrink-0',
                action.color,
                action.shadow
              ]"
            >
              {{ action.icon }}
            </div>
            <div class="min-w-0">
              <h4
                class="font-semibold text-white group-hover:text-brand-400 transition-colors"
              >
                {{ action.title }}
              </h4>
              <p class="text-xs text-surface-400 mt-0.5 leading-relaxed">
                {{ action.description }}
              </p>
            </div>
          </div>

          <!-- Arrow -->
          <div
            class="mt-3 flex items-center gap-1 text-xs text-surface-500 group-hover:text-brand-400 transition-all duration-300 group-hover:translate-x-1"
          >
            <span>Abrir</span>
            <svg
              class="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </div>
        </button>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
      <!-- Results timeline -->
      <div class="lg:col-span-2">
        <DetectionChart
          type="bar"
          title="Atividade dos Últimos 7 Dias"
          :labels="timelineChartLabels"
          :datasets="timelineChartDatasets"
          :height="240"
          :loading="loading"
          :empty="results.length === 0"
          empty-text="Nenhuma análise realizada ainda"
          empty-icon="📈"
        >
          <template #footer>
            <div
              class="flex items-center justify-between text-xs text-surface-500"
            >
              <span>{{ results.length }} resultado(s) total</span>
              <button
                @click="navigateTo('/results')"
                class="text-brand-400 hover:text-brand-300 font-medium"
              >
                Ver todos →
              </button>
            </div>
          </template>
        </DetectionChart>
      </div>

      <!-- File type distribution -->
      <div>
        <DetectionChart
          type="doughnut"
          title="Tipos de Arquivo"
          :labels="fileTypeChartLabels"
          :datasets="fileTypeChartDatasets"
          :height="240"
          :loading="loading"
          :empty="results.length === 0"
          empty-text="Sem dados"
          empty-icon="📊"
          legend-position="bottom"
        >
          <template #footer>
            <div
              class="flex items-center justify-between text-xs text-surface-500"
            >
              <span>{{ totalImages }} img · {{ totalVideos }} vid</span>
              <span>{{ fileTypeChartLabels.length }} formato(s)</span>
            </div>
          </template>
        </DetectionChart>
      </div>
    </div>

    <!-- Two-column layout: Recent Results + Active Jobs -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
      <!-- Recent Results -->
      <div class="card p-5 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="section-title">Resultados Recentes</h3>
          <button
            @click="navigateTo('/results')"
            class="btn-ghost btn-sm text-xs"
          >
            Ver todos →
          </button>
        </div>

        <div v-if="loading" class="space-y-3">
          <div
            v-for="n in 4"
            :key="n"
            class="h-12 bg-surface-700/40 rounded-xl animate-pulse"
          />
        </div>

        <div v-else-if="results.length === 0" class="text-center py-8">
          <p class="text-3xl mb-2">📭</p>
          <p class="text-sm text-surface-400">Nenhum resultado ainda</p>
          <p class="text-xs text-surface-500 mt-1">
            Analise uma imagem para começar
          </p>
        </div>

        <div v-else class="space-y-1.5 max-h-[320px] overflow-y-auto pr-1">
          <div
            v-for="item in results.slice(0, 8)"
            :key="item.name"
            class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-700/40 transition-colors group cursor-default"
          >
            <div
              :class="[
                'w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0',
                item.type === 'video'
                  ? 'bg-blue-500/10 text-blue-400'
                  : 'bg-brand-500/10 text-brand-400'
              ]"
            >
              {{ item.type === 'video' ? '🎬' : '🖼️' }}
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-surface-200 truncate">
                {{ item.name }}
              </p>
              <p class="text-[11px] text-surface-500">
                {{ formatDate(item.created) }} · {{ formatSize(item.size_kb) }}
              </p>
            </div>

            <a
              :href="item.url"
              target="_blank"
              class="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-surface-600/50 text-surface-400 hover:text-white"
              title="Abrir"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- Active Video Jobs -->
      <div class="card p-5 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="section-title">Jobs de Vídeo</h3>
          <button
            @click="navigateTo('/video')"
            class="btn-ghost btn-sm text-xs"
          >
            Processar vídeo →
          </button>
        </div>

        <div v-if="loading" class="space-y-3">
          <div
            v-for="n in 3"
            :key="n"
            class="h-16 bg-surface-700/40 rounded-xl animate-pulse"
          />
        </div>

        <div v-else-if="videoJobs.length === 0" class="text-center py-8">
          <p class="text-3xl mb-2">🎬</p>
          <p class="text-sm text-surface-400">Nenhum job de vídeo</p>
          <p class="text-xs text-surface-500 mt-1">
            Envie um vídeo para processar
          </p>
        </div>

        <div v-else class="space-y-2 max-h-[320px] overflow-y-auto pr-1">
          <div
            v-for="job in videoJobs.slice(0, 6)"
            :key="job.id"
            class="px-3.5 py-3 rounded-xl bg-surface-800/50 border border-surface-700/40"
          >
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-medium text-surface-200 truncate flex-1">
                {{ job.filename || job.id }}
              </p>
              <span :class="getJobStatusBadge(job.status).class">
                {{ getJobStatusBadge(job.status).label }}
              </span>
            </div>

            <!-- Progress bar for active jobs -->
            <div v-if="job.status === 'processing'" class="mt-2.5">
              <div class="progress-bar">
                <div
                  class="progress-fill bg-gradient-to-r from-blue-500 to-cyan-500"
                  :style="{ width: `${job.progress || 0}%` }"
                />
              </div>
              <div class="flex items-center justify-between mt-1.5">
                <span class="text-[11px] text-surface-500">
                  Frame {{ job.current_frame || 0 }}/{{
                    job.total_frames || '?'
                  }}
                </span>
                <span class="text-[11px] text-surface-500">
                  {{ (job.progress || 0).toFixed(1) }}%
                </span>
              </div>
            </div>

            <!-- Completed info -->
            <div
              v-else-if="job.status === 'completed'"
              class="mt-2 flex items-center gap-3 flex-wrap"
            >
              <span class="text-[11px] text-surface-500">
                Cobertura média: {{ job.avg_coverage }}%
              </span>
              <a
                v-if="job.output_url"
                :href="job.output_url"
                target="_blank"
                class="text-[11px] text-brand-400 hover:text-brand-300 font-medium"
              >
                Baixar vídeo →
              </a>
            </div>

            <!-- Error info -->
            <div v-else-if="job.status === 'error'" class="mt-1.5">
              <span class="text-[11px] text-red-400">{{ job.error }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- System Info (collapsed by default) -->
    <details v-if="health" class="card group">
      <summary
        class="flex items-center justify-between px-5 py-4 cursor-pointer select-none list-none hover:bg-surface-700/20 rounded-2xl transition-colors"
      >
        <div class="flex items-center gap-2.5">
          <span class="text-sm">⚙️</span>
          <h3 class="text-sm font-semibold text-surface-300">
            Informações do Sistema
          </h3>
        </div>
        <svg
          class="w-4 h-4 text-surface-500 transition-transform duration-200 group-open:rotate-180"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </summary>

      <div class="px-5 pb-5 pt-1">
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div
            v-for="(available, component) in health.components"
            :key="component"
            class="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-800/40"
          >
            <div
              :class="[
                'w-2 h-2 rounded-full shrink-0',
                available ? 'bg-brand-500' : 'bg-surface-500'
              ]"
            />
            <span class="text-xs text-surface-300 capitalize truncate">{{
              component
            }}</span>
          </div>
        </div>
        <p class="text-xs text-surface-500 mt-3">
          Output:
          <code class="text-surface-400 font-mono text-[11px]">{{
            health.output_dir
          }}</code>
        </p>
      </div>
    </details>
  </div>
</template>
