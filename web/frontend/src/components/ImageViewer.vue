<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  src: {
    type: String,
    default: '',
  },
  alt: {
    type: String,
    default: 'Imagem',
  },
  caption: {
    type: String,
    default: '',
  },
  downloadFilename: {
    type: String,
    default: '',
  },
  downloadUrl: {
    type: String,
    default: '',
  },
  maxHeight: {
    type: String,
    default: '400px',
  },
  rounded: {
    type: Boolean,
    default: true,
  },
  border: {
    type: Boolean,
    default: true,
  },
  zoomable: {
    type: Boolean,
    default: true,
  },
  downloadable: {
    type: Boolean,
    default: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '🖼️',
  },
  placeholderText: {
    type: String,
    default: 'Nenhuma imagem disponível',
  },
  badges: {
    type: Array,
    default: () => [],
    // { label, color? }
  },
  compact: {
    type: Boolean,
    default: false,
  },
  objectFit: {
    type: String,
    default: 'contain',
    validator: (v) => ['contain', 'cover', 'fill', 'none', 'scale-down'].includes(v),
  },
})

const emit = defineEmits(['open', 'close', 'download', 'error'])

const lightboxOpen = ref(false)
const imageLoaded = ref(false)
const imageError = ref(false)
const zoom = ref(1)
const pan = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const lightboxImageRef = ref(null)

const MIN_ZOOM = 0.5
const MAX_ZOOM = 5
const ZOOM_STEP = 0.3

const hasSrc = computed(() => !!props.src)
const hasError = computed(() => !!props.error || imageError.value)
const isReady = computed(() => hasSrc.value && imageLoaded.value && !hasError.value)

const resolvedDownloadUrl = computed(() => props.downloadUrl || props.src)

const objectFitClass = computed(() => {
  const map = {
    contain: 'object-contain',
    cover: 'object-cover',
    fill: 'object-fill',
    none: 'object-none',
    'scale-down': 'object-scale-down',
  }
  return map[props.objectFit] || 'object-contain'
})

const badgeColorMap = {
  brand: 'bg-brand-500/80 text-white',
  blue: 'bg-blue-500/80 text-white',
  purple: 'bg-purple-500/80 text-white',
  orange: 'bg-orange-500/80 text-white',
  red: 'bg-red-500/80 text-white',
  yellow: 'bg-yellow-500/80 text-black',
  teal: 'bg-teal-500/80 text-white',
  pink: 'bg-pink-500/80 text-white',
  surface: 'bg-surface-700/90 text-surface-200',
  green: 'bg-brand-500/80 text-white',
}

function onImageLoad() {
  imageLoaded.value = true
  imageError.value = false
}

function onImageError() {
  imageLoaded.value = false
  imageError.value = true
  emit('error', 'Falha ao carregar imagem')
}

function openLightbox() {
  if (!props.zoomable || !isReady.value) return
  lightboxOpen.value = true
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
  emit('open')
  document.body.style.overflow = 'hidden'
}

function closeLightbox() {
  lightboxOpen.value = false
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
  isDragging.value = false
  emit('close')
  document.body.style.overflow = ''
}

function zoomIn() {
  zoom.value = Math.min(MAX_ZOOM, zoom.value + ZOOM_STEP)
}

function zoomOut() {
  zoom.value = Math.max(MIN_ZOOM, zoom.value - ZOOM_STEP)
}

function resetZoom() {
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
}

function fitToScreen() {
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
}

function onWheel(event) {
  if (!lightboxOpen.value) return
  event.preventDefault()
  const delta = event.deltaY > 0 ? -ZOOM_STEP * 0.5 : ZOOM_STEP * 0.5
  zoom.value = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom.value + delta))
}

function onMouseDown(event) {
  if (zoom.value <= 1) return
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - pan.value.x,
    y: event.clientY - pan.value.y,
  }
  event.preventDefault()
}

function onMouseMove(event) {
  if (!isDragging.value) return
  pan.value = {
    x: event.clientX - dragStart.value.x,
    y: event.clientY - dragStart.value.y,
  }
}

function onMouseUp() {
  isDragging.value = false
}

function onTouchStart(event) {
  if (zoom.value <= 1 || event.touches.length !== 1) return
  isDragging.value = true
  const touch = event.touches[0]
  dragStart.value = {
    x: touch.clientX - pan.value.x,
    y: touch.clientY - pan.value.y,
  }
}

function onTouchMove(event) {
  if (!isDragging.value || event.touches.length !== 1) return
  event.preventDefault()
  const touch = event.touches[0]
  pan.value = {
    x: touch.clientX - dragStart.value.x,
    y: touch.clientY - dragStart.value.y,
  }
}

function onTouchEnd() {
  isDragging.value = false
}

function download() {
  if (!resolvedDownloadUrl.value) return

  const link = document.createElement('a')
  link.href = resolvedDownloadUrl.value
  link.download = props.downloadFilename || 'image'
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  emit('download', resolvedDownloadUrl.value)
}

function openInNewTab() {
  if (!props.src) return
  const win = window.open()
  if (win) {
    win.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${props.alt || 'Imagem'}</title>
          <style>
            body { margin: 0; background: #0a0a0a; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            img { max-width: 100%; max-height: 100vh; object-fit: contain; }
          </style>
        </head>
        <body>
          <img src="${props.src}" alt="${props.alt || 'Imagem'}" />
        </body>
      </html>
    `)
    win.document.close()
  }
}

function onKeydown(event) {
  if (!lightboxOpen.value) return

  switch (event.key) {
    case 'Escape':
      event.preventDefault()
      closeLightbox()
      break
    case '+':
    case '=':
      event.preventDefault()
      zoomIn()
      break
    case '-':
      event.preventDefault()
      zoomOut()
      break
    case '0':
      event.preventDefault()
      resetZoom()
      break
    case 'd':
    case 'D':
      if (!event.ctrlKey && !event.metaKey) {
        event.preventDefault()
        download()
      }
      break
  }
}

watch(
  () => props.src,
  () => {
    imageLoaded.value = false
    imageError.value = false
  }
)

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  if (lightboxOpen.value) {
    document.body.style.overflow = ''
  }
})

const lightboxTransform = computed(() => {
  return `scale(${zoom.value}) translate(${pan.value.x / zoom.value}px, ${pan.value.y / zoom.value}px)`
})

const zoomPercent = computed(() => Math.round(zoom.value * 100))
</script>

<template>
  <div class="relative group">
    <!-- ═══ Loading state ═══ -->
    <div
      v-if="loading"
      :class="[
        'flex flex-col items-center justify-center bg-surface-800/40',
        rounded ? 'rounded-xl' : '',
        border ? 'border border-surface-700/50' : '',
      ]"
      :style="{ minHeight: compact ? '120px' : '200px', maxHeight }"
    >
      <svg
        class="animate-spin w-8 h-8 text-surface-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="3"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <p class="text-xs text-surface-500 mt-3 font-medium">Carregando imagem...</p>
    </div>

    <!-- ═══ Error state ═══ -->
    <div
      v-else-if="hasError"
      :class="[
        'flex flex-col items-center justify-center bg-red-500/5',
        rounded ? 'rounded-xl' : '',
        border ? 'border border-red-500/20' : '',
      ]"
      :style="{ minHeight: compact ? '120px' : '200px', maxHeight }"
    >
      <div class="w-12 h-12 flex items-center justify-center rounded-xl bg-red-500/10 border border-red-500/15 text-2xl mb-3">
        ❌
      </div>
      <p class="text-sm font-medium text-red-400">Erro ao carregar imagem</p>
      <p v-if="error" class="text-xs text-red-400/60 mt-1 max-w-xs text-center px-4">
        {{ error }}
      </p>
    </div>

    <!-- ═══ Empty state (no src) ═══ -->
    <div
      v-else-if="!hasSrc"
      :class="[
        'flex flex-col items-center justify-center bg-surface-800/30',
        rounded ? 'rounded-xl' : '',
        border ? 'border border-dashed border-surface-700/50' : '',
      ]"
      :style="{ minHeight: compact ? '120px' : '200px', maxHeight }"
    >
      <div class="w-12 h-12 flex items-center justify-center rounded-xl bg-surface-800/60 border border-surface-700/50 text-2xl mb-3">
        {{ placeholder }}
      </div>
      <p class="text-sm font-medium text-surface-400">{{ placeholderText }}</p>
    </div>

    <!-- ═══ Image display ═══ -->
    <div
      v-else
      :class="[
        'relative overflow-hidden',
        rounded ? 'rounded-xl' : '',
        border ? 'border border-surface-700/50' : '',
        zoomable && isReady ? 'cursor-zoom-in' : '',
      ]"
    >
      <!-- Loading shimmer while image hasn't loaded -->
      <div
        v-if="!imageLoaded && !imageError"
        class="absolute inset-0 bg-surface-800/60 animate-pulse flex items-center justify-center"
        :style="{ minHeight: compact ? '120px' : '200px' }"
      >
        <svg
          class="animate-spin w-6 h-6 text-surface-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>

      <!-- Actual image -->
      <img
        :src="src"
        :alt="alt"
        :class="[
          'w-full transition-opacity duration-300',
          objectFitClass,
          imageLoaded ? 'opacity-100' : 'opacity-0',
        ]"
        :style="{ maxHeight }"
        @load="onImageLoad"
        @error="onImageError"
        @click="openLightbox"
      />

      <!-- Badges overlay (top-left) -->
      <div
        v-if="badges.length > 0 && isReady"
        class="absolute top-2 left-2 flex flex-wrap gap-1.5"
      >
        <span
          v-for="(badge, idx) in badges"
          :key="idx"
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold backdrop-blur-sm shadow-sm',
            badgeColorMap[badge.color || 'surface'] || badgeColorMap.surface,
          ]"
        >
          {{ badge.label }}
        </span>
      </div>

      <!-- Actions overlay (bottom bar on hover) -->
      <Transition name="fade">
        <div
          v-if="isReady && (zoomable || downloadable)"
          class="absolute inset-x-0 bottom-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <div
            class="flex items-center justify-between gap-2 px-3 py-2 bg-gradient-to-t from-black/70 via-black/40 to-transparent"
          >
            <!-- Caption -->
            <p
              v-if="caption"
              class="text-xs text-white/80 font-medium truncate flex-1 min-w-0"
            >
              {{ caption }}
            </p>
            <div v-else class="flex-1" />

            <!-- Action buttons -->
            <div class="flex items-center gap-1.5 shrink-0">
              <button
                v-if="zoomable"
                @click.stop="openLightbox"
                class="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-all backdrop-blur-sm"
                title="Ampliar imagem"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              </button>

              <button
                v-if="downloadable && resolvedDownloadUrl"
                @click.stop="download"
                class="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-all backdrop-blur-sm"
                title="Baixar imagem"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>

              <button
                @click.stop="openInNewTab"
                class="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-all backdrop-blur-sm"
                title="Abrir em nova aba"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Default slot overlay (custom overlays) -->
      <slot :is-ready="isReady" :open-lightbox="openLightbox" :download="download" />
    </div>

    <!-- ═══ Lightbox ═══ -->
    <Teleport to="body">
      <Transition name="lightbox">
        <div
          v-if="lightboxOpen"
          class="fixed inset-0 z-[9998] flex items-center justify-center"
          @wheel.prevent="onWheel"
        >
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/90 backdrop-blur-md"
            @click="closeLightbox"
          />

          <!-- Top bar -->
          <div class="absolute top-0 inset-x-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/60 to-transparent">
            <!-- Left: info -->
            <div class="flex items-center gap-3 min-w-0">
              <p
                v-if="caption || alt"
                class="text-sm font-medium text-white/80 truncate"
              >
                {{ caption || alt }}
              </p>
              <span class="text-xs text-white/40 font-mono tabular-nums shrink-0">
                {{ zoomPercent }}%
              </span>
            </div>

            <!-- Right: actions -->
            <div class="flex items-center gap-1.5 shrink-0">
              <button
                @click="zoomOut"
                :disabled="zoom <= MIN_ZOOM"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-30 disabled:pointer-events-none"
                title="Diminuir zoom (−)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                </svg>
              </button>

              <button
                @click="zoomIn"
                :disabled="zoom >= MAX_ZOOM"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-30 disabled:pointer-events-none"
                title="Aumentar zoom (+)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              </button>

              <button
                @click="resetZoom"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                title="Resetar zoom (0)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>

              <div class="w-px h-5 bg-white/15 mx-1" />

              <button
                v-if="downloadable && resolvedDownloadUrl"
                @click="download"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                title="Baixar imagem (D)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>

              <button
                @click="openInNewTab"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                title="Abrir em nova aba"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>

              <div class="w-px h-5 bg-white/15 mx-1" />

              <button
                @click="closeLightbox"
                class="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                title="Fechar (Esc)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Image container -->
          <div
            class="relative flex items-center justify-center w-full h-full p-12 select-none"
            :class="[
              zoom > 1 ? 'cursor-grab' : 'cursor-zoom-out',
              isDragging ? 'cursor-grabbing' : '',
            ]"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
            @touchstart.passive="onTouchStart"
            @touchmove="onTouchMove"
            @touchend="onTouchEnd"
            @click.self="closeLightbox"
          >
            <img
              ref="lightboxImageRef"
              :src="src"
              :alt="alt"
              class="max-w-full max-h-full object-contain transition-transform duration-150 ease-out pointer-events-none select-none"
              :style="{ transform: lightboxTransform }"
              draggable="false"
            />
          </div>

          <!-- Bottom hint bar -->
          <div class="absolute bottom-0 inset-x-0 z-10 flex items-center justify-center px-4 py-3 bg-gradient-to-t from-black/40 to-transparent pointer-events-none">
            <div class="flex items-center gap-4 text-[10px] text-white/30 font-medium">
              <span>Scroll para zoom</span>
              <span>•</span>
              <span>Arraste para mover</span>
              <span>•</span>
              <span>Esc para fechar</span>
              <span v-if="downloadable">•</span>
              <span v-if="downloadable">D para baixar</span>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.lightbox-enter-active {
  transition: opacity 0.3s ease-out;
}

.lightbox-leave-active {
  transition: opacity 0.25s ease-in;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-active img {
  transition: transform 0.3s cubic-bezier(0.21, 1.02, 0.73, 1);
}

.lightbox-enter-from img {
  transform: scale(0.9);
}
</style>
