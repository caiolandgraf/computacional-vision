<script setup>
import { ref, computed, onMounted } from 'vue'
import { listResults, deleteResult, getDownloadUrl, getFileUrl } from '@/services/api'

const results = ref([])
const loading = ref(true)
const error = ref(null)
const filter = ref('all')
const sortBy = ref('date')
const searchQuery = ref('')
const selectedItem = ref(null)
const showDeleteConfirm = ref(false)
const itemToDelete = ref(null)
const deleting = ref(false)
const lightboxOpen = ref(false)
const lightboxSrc = ref('')

const filteredResults = computed(() => {
  let items = [...results.value]

  // Filter by type
  if (filter.value === 'image') {
    items = items.filter((r) => r.type === 'image')
  } else if (filter.value === 'video') {
    items = items.filter((r) => r.type === 'video')
  }

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    items = items.filter((r) => r.name.toLowerCase().includes(q))
  }

  // Sort
  if (sortBy.value === 'date') {
    items.sort((a, b) => new Date(b.created).getTime() - new Date(a.created).getTime())
  } else if (sortBy.value === 'name') {
    items.sort((a, b) => a.name.localeCompare(b.name))
  } else if (sortBy.value === 'size') {
    items.sort((a, b) => b.size_kb - a.size_kb)
  }

  return items
})

const totalImages = computed(() => results.value.filter((r) => r.type === 'image').length)
const totalVideos = computed(() => results.value.filter((r) => r.type === 'video').length)
const totalSizeKb = computed(() => results.value.reduce((sum, r) => sum + (r.size_kb || 0), 0))

const totalSizeFormatted = computed(() => {
  const kb = totalSizeKb.value
  if (kb > 1024 * 1024) return `${(kb / (1024 * 1024)).toFixed(1)} GB`
  if (kb > 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(0)} KB`
})

const filterCounts = computed(() => ({
  all: results.value.length,
  image: totalImages.value,
  video: totalVideos.value,
}))

async function loadResults() {
  loading.value = true
  error.value = null
  try {
    const data = await listResults(200)
    results.value = data.results || []
  } catch (err) {
    error.value = err.message || 'Erro ao carregar resultados'
  } finally {
    loading.value = false
  }
}

function formatDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatRelativeDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffSec < 60) return 'Agora mesmo'
  if (diffMin < 60) return `${diffMin}min atrás`
  if (diffHr < 24) return `${diffHr}h atrás`
  if (diffDay < 7) return `${diffDay}d atrás`
  return formatDate(isoString)
}

function formatSize(kb) {
  if (!kb) return '0 B'
  if (kb > 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(0)} KB`
}

function getFileIcon(item) {
  if (item.type === 'video') return '🎬'
  if (item.name.includes('overlay')) return '🌿'
  if (item.name.includes('pothole')) return '🕳️'
  if (item.name.includes('comparison') || item.name.includes('compare')) return '🔬'
  if (item.name.includes('batch')) return '📁'
  if (item.name.includes('detailed')) return '📊'
  if (item.name.includes('webcam')) return '📹'
  return '🖼️'
}

function getFileBadge(item) {
  if (item.type === 'video') return { cls: 'badge-blue', label: 'Vídeo' }
  if (item.name.includes('overlay')) return { cls: 'badge-green', label: 'Overlay' }
  if (item.name.includes('pothole')) return { cls: 'badge bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/20', label: 'Buracos' }
  if (item.name.includes('comparison') || item.name.includes('compare')) return { cls: 'badge bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/20', label: 'Comparação' }
  if (item.name.includes('batch')) return { cls: 'badge bg-pink-500/15 text-pink-400 ring-1 ring-pink-500/20', label: 'Lote' }
  if (item.name.includes('detailed')) return { cls: 'badge bg-purple-500/15 text-purple-400 ring-1 ring-purple-500/20', label: 'Detalhado' }
  return { cls: 'badge-surface', label: 'Imagem' }
}

function selectItem(item) {
  selectedItem.value = item
}

function openLightbox(item) {
  if (item.type === 'video') {
    window.open(item.url, '_blank')
    return
  }
  lightboxSrc.value = item.url
  lightboxOpen.value = true
}

function closeLightbox() {
  lightboxOpen.value = false
  lightboxSrc.value = ''
}

function downloadItem(item) {
  const link = document.createElement('a')
  link.href = getDownloadUrl(item.name)
  link.download = item.name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function confirmDelete(item) {
  itemToDelete.value = item
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!itemToDelete.value) return

  deleting.value = true
  try {
    await deleteResult(itemToDelete.value.name)
    results.value = results.value.filter((r) => r.name !== itemToDelete.value.name)
    if (selectedItem.value?.name === itemToDelete.value.name) {
      selectedItem.value = null
    }
    showDeleteConfirm.value = false
    itemToDelete.value = null
  } catch (err) {
    error.value = err.message || 'Erro ao deletar arquivo'
  } finally {
    deleting.value = false
  }
}

function cancelDelete() {
  showDeleteConfirm.value = false
  itemToDelete.value = null
}

function isImageFile(item) {
  return item.type === 'image'
}

onMounted(loadResults)
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white">Resultados</h1>
        <p class="text-sm text-surface-400 mt-1">
          Galeria de todos os resultados gerados pelo sistema de detecção.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button @click="loadResults" :disabled="loading" class="btn-secondary btn-sm">
          <svg
            :class="['w-4 h-4', loading && 'animate-spin']"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Atualizar
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div
      v-if="error"
      class="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
    >
      <span class="text-lg">⚠️</span>
      <div class="flex-1">
        <p class="font-semibold">Erro</p>
        <p class="text-red-400/70 text-xs mt-0.5">{{ error }}</p>
      </div>
      <button @click="error = null" class="btn-ghost btn-sm text-red-400">✕</button>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="stat-card animate-in stagger-1">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-surface-700/60 flex items-center justify-center text-xs">📊</div>
          <span class="stat-label">Total</span>
        </div>
        <span class="stat-value text-surface-100 mt-1.5">{{ results.length }}</span>
      </div>

      <div class="stat-card animate-in stagger-2">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-brand-500/10 flex items-center justify-center text-xs">🖼️</div>
          <span class="stat-label">Imagens</span>
        </div>
        <span class="stat-value text-brand-400 mt-1.5">{{ totalImages }}</span>
      </div>

      <div class="stat-card animate-in stagger-3">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center text-xs">🎬</div>
          <span class="stat-label">Vídeos</span>
        </div>
        <span class="stat-value text-blue-400 mt-1.5">{{ totalVideos }}</span>
      </div>

      <div class="stat-card animate-in stagger-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center text-xs">💾</div>
          <span class="stat-label">Tamanho Total</span>
        </div>
        <span class="stat-value text-amber-400 mt-1.5 text-lg">{{ totalSizeFormatted }}</span>
      </div>
    </div>

    <!-- Toolbar: Search, Filter, Sort -->
    <div class="card p-4">
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <!-- Search -->
        <div class="relative flex-1">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500 pointer-events-none"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Buscar por nome..."
            class="input pl-10"
          />
        </div>

        <!-- Filter Tabs -->
        <div class="flex items-center gap-1 bg-surface-800/60 rounded-xl p-1">
          <button
            v-for="f in [
              { value: 'all', label: 'Todos', icon: '📊' },
              { value: 'image', label: 'Imagens', icon: '🖼️' },
              { value: 'video', label: 'Vídeos', icon: '🎬' },
            ]"
            :key="f.value"
            @click="filter = f.value"
            :class="[
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200',
              filter === f.value
                ? 'bg-surface-700 text-white shadow-sm'
                : 'text-surface-400 hover:text-surface-200',
            ]"
          >
            <span class="text-sm">{{ f.icon }}</span>
            <span>{{ f.label }}</span>
            <span
              :class="[
                'px-1.5 py-0.5 rounded-md text-[10px] font-bold',
                filter === f.value
                  ? 'bg-surface-600 text-surface-200'
                  : 'bg-surface-800/60 text-surface-500',
              ]"
            >
              {{ filterCounts[f.value] }}
            </span>
          </button>
        </div>

        <!-- Sort -->
        <select v-model="sortBy" class="select w-auto min-w-[140px]">
          <option value="date">Mais recentes</option>
          <option value="name">Nome A-Z</option>
          <option value="size">Maior tamanho</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div
        v-for="n in 8"
        :key="n"
        class="card overflow-hidden animate-pulse"
      >
        <div class="aspect-video bg-surface-700/40" />
        <div class="p-3.5 space-y-2">
          <div class="h-4 bg-surface-700/40 rounded w-3/4" />
          <div class="h-3 bg-surface-700/40 rounded w-1/2" />
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="results.length === 0"
      class="card p-16 flex flex-col items-center justify-center text-center"
    >
      <div class="text-5xl mb-4">📭</div>
      <h3 class="text-lg font-semibold text-surface-300">Nenhum resultado encontrado</h3>
      <p class="text-sm text-surface-500 mt-1 max-w-md">
        Os resultados aparecerão aqui após você analisar imagens, processar vídeos ou usar a webcam.
      </p>
    </div>

    <!-- No matches state -->
    <div
      v-else-if="filteredResults.length === 0"
      class="card p-12 flex flex-col items-center justify-center text-center"
    >
      <div class="text-4xl mb-3">🔍</div>
      <h3 class="text-base font-semibold text-surface-300">Nenhum resultado encontrado</h3>
      <p class="text-sm text-surface-500 mt-1">
        Tente alterar os filtros ou o termo de busca.
      </p>
      <button
        @click="filter = 'all'; searchQuery = ''"
        class="btn-secondary btn-sm mt-4"
      >
        Limpar filtros
      </button>
    </div>

    <!-- Results Grid -->
    <div
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <div
        v-for="(item, idx) in filteredResults"
        :key="item.name"
        :class="[
          'card-hover overflow-hidden cursor-pointer group animate-in',
          `stagger-${Math.min(idx + 1, 6)}`,
          selectedItem?.name === item.name && 'ring-2 ring-brand-500/50',
        ]"
        @click="selectItem(item)"
      >
        <!-- Thumbnail -->
        <div class="relative aspect-video bg-surface-800/60 overflow-hidden">
          <!-- Image Thumbnail -->
          <img
            v-if="isImageFile(item)"
            :src="item.url"
            :alt="item.name"
            class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            @error="($event.target).style.display = 'none'"
          />

          <!-- Video Thumbnail Placeholder -->
          <div
            v-else
            class="w-full h-full flex items-center justify-center bg-gradient-to-br from-surface-800 to-surface-900"
          >
            <div class="text-center">
              <div class="text-4xl mb-1">🎬</div>
              <span class="text-xs text-surface-500">Vídeo</span>
            </div>
          </div>

          <!-- Hover Actions Overlay -->
          <div
            class="absolute inset-0 bg-black/50 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-2"
          >
            <button
              @click.stop="openLightbox(item)"
              class="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors"
              :title="item.type === 'video' ? 'Abrir vídeo' : 'Ampliar'"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6"
                />
              </svg>
            </button>

            <button
              @click.stop="downloadItem(item)"
              class="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors"
              title="Download"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
            </button>

            <button
              @click.stop="confirmDelete(item)"
              class="p-2.5 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-300 transition-colors"
              title="Deletar"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                />
              </svg>
            </button>
          </div>

          <!-- Type Badge (top-left) -->
          <div class="absolute top-2 left-2">
            <span :class="getFileBadge(item).cls" class="text-[10px] shadow-lg">
              {{ getFileBadge(item).label }}
            </span>
          </div>

          <!-- Size Badge (top-right) -->
          <div class="absolute top-2 right-2">
            <span class="badge bg-black/50 backdrop-blur-sm text-surface-200 text-[10px]">
              {{ formatSize(item.size_kb) }}
            </span>
          </div>
        </div>

        <!-- File Info -->
        <div class="p-3.5">
          <div class="flex items-start gap-2">
            <span class="text-base shrink-0 mt-0.5">{{ getFileIcon(item) }}</span>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-surface-200 truncate leading-tight" :title="item.name">
                {{ item.name }}
              </p>
              <p class="text-[11px] text-surface-500 mt-1">
                {{ formatRelativeDate(item.created) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Results count -->
    <div
      v-if="!loading && filteredResults.length > 0"
      class="text-center text-xs text-surface-500 py-2"
    >
      Mostrando {{ filteredResults.length }}
      {{ filteredResults.length === 1 ? 'resultado' : 'resultados' }}
      <template v-if="filter !== 'all' || searchQuery.trim()">
        (de {{ results.length }} no total)
      </template>
    </div>

    <!-- Selected Item Detail Panel -->
    <Transition name="slide">
      <div
        v-if="selectedItem"
        class="card p-5 space-y-4"
      >
        <div class="flex items-center justify-between">
          <h3 class="section-title flex items-center gap-2">
            <span>{{ getFileIcon(selectedItem) }}</span>
            Detalhes do Arquivo
          </h3>
          <button
            @click="selectedItem = null"
            class="p-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-3 text-sm">
          <div>
            <span class="text-xs text-surface-500 block mb-0.5">Nome</span>
            <p class="text-surface-200 font-medium break-all text-xs">{{ selectedItem.name }}</p>
          </div>
          <div>
            <span class="text-xs text-surface-500 block mb-0.5">Tipo</span>
            <span :class="getFileBadge(selectedItem).cls">
              {{ getFileBadge(selectedItem).label }}
            </span>
          </div>
          <div>
            <span class="text-xs text-surface-500 block mb-0.5">Tamanho</span>
            <p class="text-surface-200 font-medium">{{ formatSize(selectedItem.size_kb) }}</p>
          </div>
          <div>
            <span class="text-xs text-surface-500 block mb-0.5">Criado em</span>
            <p class="text-surface-200 font-medium text-xs">{{ formatDate(selectedItem.created) }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2 border-t border-surface-700/50">
          <a
            :href="selectedItem.url"
            target="_blank"
            class="btn-secondary btn-sm text-xs"
          >
            🔗 Abrir em Nova Aba
          </a>
          <button @click="downloadItem(selectedItem)" class="btn-secondary btn-sm text-xs">
            ⬇️ Download
          </button>
          <button @click="openLightbox(selectedItem)" class="btn-secondary btn-sm text-xs">
            🔍 {{ selectedItem.type === 'video' ? 'Reproduzir' : 'Ampliar' }}
          </button>
          <div class="flex-1" />
          <button @click="confirmDelete(selectedItem)" class="btn-danger btn-sm text-xs">
            🗑️ Deletar
          </button>
        </div>
      </div>
    </Transition>

    <!-- Lightbox Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="lightboxOpen"
          class="fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 sm:p-8"
          @click.self="closeLightbox"
        >
          <!-- Close button -->
          <button
            @click="closeLightbox"
            class="absolute top-4 right-4 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors z-10"
          >
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Image -->
          <img
            :src="lightboxSrc"
            alt="Lightbox"
            class="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-in"
          />
        </div>
      </Transition>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showDeleteConfirm"
          class="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          @click.self="cancelDelete"
        >
          <div class="card p-6 max-w-sm w-full space-y-4 animate-in shadow-2xl">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-xl bg-red-500/10 flex items-center justify-center text-xl shrink-0">
                🗑️
              </div>
              <div>
                <h3 class="text-base font-bold text-white">Confirmar Exclusão</h3>
                <p class="text-xs text-surface-400 mt-0.5">Esta ação não pode ser desfeita.</p>
              </div>
            </div>

            <div class="px-3 py-2.5 rounded-xl bg-surface-800/60 border border-surface-700/50">
              <div class="flex items-center gap-2.5">
                <span class="text-base">{{ getFileIcon(itemToDelete) }}</span>
                <div class="min-w-0">
                  <p class="text-sm font-medium text-surface-200 truncate">{{ itemToDelete?.name }}</p>
                  <p class="text-[11px] text-surface-500">{{ formatSize(itemToDelete?.size_kb) }}</p>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 pt-1">
              <button
                @click="cancelDelete"
                :disabled="deleting"
                class="btn-secondary flex-1 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                @click="executeDelete"
                :disabled="deleting"
                class="btn-danger flex-1 disabled:opacity-50"
              >
                <template v-if="deleting">
                  <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Deletando...
                </template>
                <template v-else>
                  Deletar
                </template>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
