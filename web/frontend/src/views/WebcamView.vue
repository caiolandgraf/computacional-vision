<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import {
  createWebcamSocket,
  GRASS_METHODS,
  WEBCAM_VISUAL_MODES,
  WEBCAM_QUALITY_MODES
} from '@/services/api'

const videoRef = ref(null)
const canvasRef = ref(null)
const method = ref('combined')
const visualMode = ref('fast')
const qualityMode = ref('1')
const isStreaming = ref(false)
const isConnected = ref(false)
const error = ref(null)
const lastResult = ref(null)
const resultImage = ref(null)
const showOverlay = ref(true)
const frameInterval = ref(200)
const showShortcuts = ref(false)
const stats = ref({
  coverage: 0,
  regions: 0,
  processingTime: 0,
  fps: 0,
  serverFps: 0
})

let socket = null
let stream = null
let sendTimer = null
let fpsCounter = 0
let fpsTimer = null
let cameras = ref([])
let selectedCamera = ref('')

const coverageColor = computed(() => {
  const c = stats.value.coverage
  if (c >= 60) return 'text-red-400'
  if (c >= 30) return 'text-orange-400'
  if (c >= 10) return 'text-yellow-400'
  return 'text-brand-400'
})

const coverageBarColor = computed(() => {
  const c = stats.value.coverage
  if (c >= 60) return 'bg-gradient-to-r from-red-500 to-orange-500'
  if (c >= 30) return 'bg-gradient-to-r from-orange-500 to-yellow-500'
  return 'bg-gradient-to-r from-brand-500 to-emerald-500'
})

const coverageLabel = computed(() => {
  const c = stats.value.coverage
  if (c >= 60) return 'Muito Alto'
  if (c >= 30) return 'Alto'
  if (c >= 10) return 'Moderado'
  return 'Baixo'
})

const selectedMethodLabel = computed(
  () => GRASS_METHODS.find(m => m.value === method.value)?.label || method.value
)

const selectedVisualLabel = computed(
  () =>
    WEBCAM_VISUAL_MODES.find(m => m.value === visualMode.value)?.label ||
    visualMode.value
)

const selectedQualityLabel = computed(
  () =>
    WEBCAM_QUALITY_MODES.find(m => m.value === qualityMode.value)?.label ||
    qualityMode.value
)

async function listCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices
      .filter(d => d.kind === 'videoinput')
      .map((d, i) => ({
        id: d.deviceId,
        label: d.label || `Câmera ${i + 1}`
      }))
    if (cameras.value.length > 0 && !selectedCamera.value) {
      selectedCamera.value = cameras.value[0].id
    }
  } catch (err) {
    console.error('Erro ao listar câmeras:', err)
  }
}

async function startWebcam() {
  error.value = null

  try {
    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 15 }
      }
    }
    if (selectedCamera.value) {
      constraints.video.deviceId = { exact: selectedCamera.value }
    }

    stream = await navigator.mediaDevices.getUserMedia(constraints)

    if (videoRef.value) {
      videoRef.value.srcObject = stream
      await videoRef.value.play()
    }

    isStreaming.value = true
    connectWebSocket()
  } catch (err) {
    console.error('Erro ao acessar webcam:', err)
    if (err.name === 'NotAllowedError') {
      error.value =
        'Permissão de câmera negada. Verifique as permissões do navegador.'
    } else if (err.name === 'NotFoundError') {
      error.value = 'Nenhuma câmera encontrada no dispositivo.'
    } else {
      error.value = `Erro ao acessar câmera: ${err.message}`
    }
  }
}

function stopWebcam() {
  isStreaming.value = false

  if (sendTimer) {
    clearInterval(sendTimer)
    sendTimer = null
  }

  if (fpsTimer) {
    clearInterval(fpsTimer)
    fpsTimer = null
  }

  if (socket) {
    socket.close()
    socket = null
  }

  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null
  }

  isConnected.value = false
  resultImage.value = null
  lastResult.value = null
  stats.value = {
    coverage: 0,
    regions: 0,
    processingTime: 0,
    fps: 0,
    serverFps: 0
  }
}

function sendCurrentConfig() {
  if (socket?.isConnected) {
    socket.sendConfig({
      method: method.value,
      visualMode: visualMode.value,
      qualityMode: qualityMode.value
    })
  }
}

function connectWebSocket() {
  socket = createWebcamSocket({
    onOpen() {
      isConnected.value = true
      error.value = null

      // Envia config inicial
      sendCurrentConfig()

      // Começa a enviar frames
      startSendingFrames()

      // Contador de FPS do cliente
      fpsCounter = 0
      fpsTimer = setInterval(() => {
        stats.value.fps = fpsCounter
        fpsCounter = 0
      }, 1000)
    },
    onResult(msg) {
      if (msg.image) {
        resultImage.value = `data:image/jpeg;base64,${msg.image}`
      }
      if (msg.stats) {
        stats.value.coverage = msg.stats.coverage || 0
        stats.value.regions = msg.stats.regions || 0
        stats.value.processingTime = msg.stats.processing_time_ms || 0
        if (msg.stats.fps !== undefined) {
          stats.value.serverFps = msg.stats.fps
        }
      }
      lastResult.value = msg
      fpsCounter++
    },
    onClose() {
      isConnected.value = false
    },
    onError() {
      isConnected.value = false
      if (isStreaming.value) {
        error.value =
          'Conexão WebSocket perdida. Verifique se o servidor está rodando.'
      }
    }
  })
}

function startSendingFrames() {
  if (sendTimer) clearInterval(sendTimer)

  sendTimer = setInterval(() => {
    if (!isStreaming.value || !socket?.isConnected || !videoRef.value) return

    const video = videoRef.value
    const canvas = canvasRef.value
    if (!canvas || !video.videoWidth) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.7)
    const base64 = dataUrl.split(',')[1]

    socket.sendFrame(base64)
  }, frameInterval.value)
}

function updateMethod(newMethod) {
  method.value = newMethod
  sendCurrentConfig()
}

function updateVisualMode(newMode) {
  visualMode.value = newMode
  sendCurrentConfig()
}

function updateQualityMode(newMode) {
  qualityMode.value = newMode
  sendCurrentConfig()
}

function cycleVisualMode() {
  const modes = WEBCAM_VISUAL_MODES.map(m => m.value)
  const idx = modes.indexOf(visualMode.value)
  const next = modes[(idx + 1) % modes.length]
  updateVisualMode(next)
}

function toggleQualityMode() {
  const next = qualityMode.value === '1' ? '2' : '1'
  updateQualityMode(next)
}

function updateFrameRate(ms) {
  frameInterval.value = ms
  if (isStreaming.value && sendTimer) {
    startSendingFrames()
  }
}

function takeSnapshot() {
  if (!resultImage.value) return
  const link = document.createElement('a')
  link.download = `webcam_snapshot_${new Date().toISOString().replace(/[:.]/g, '-')}.jpg`
  link.href = resultImage.value
  link.click()
}

function handleKeydown(e) {
  // Não captura se o foco está em um input/select/textarea
  const tag = e.target.tagName.toLowerCase()
  if (tag === 'input' || tag === 'select' || tag === 'textarea') return

  switch (e.key.toLowerCase()) {
    case 'v':
      e.preventDefault()
      cycleVisualMode()
      break
    case 'm':
      e.preventDefault()
      toggleQualityMode()
      break
    case 's':
      e.preventDefault()
      takeSnapshot()
      break
    case 'h':
      e.preventDefault()
      showShortcuts.value = !showShortcuts.value
      break
    case 'escape':
      if (showShortcuts.value) {
        showShortcuts.value = false
      }
      break
  }
}

onMounted(() => {
  listCameras()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  stopWebcam()
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white">
          Webcam Tempo Real
        </h1>
        <p class="text-sm text-surface-400 mt-1">
          Analise mato alto em tempo real usando a webcam. Pressione
          <kbd class="kbd">V</kbd> para trocar visualização ou
          <kbd class="kbd">H</kbd> para ver atalhos.
        </p>
      </div>

      <!-- Keyboard shortcuts button -->
      <button
        @click="showShortcuts = !showShortcuts"
        :class="[
          'flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all duration-200',
          showShortcuts
            ? 'bg-brand-600/20 border border-brand-500/30 text-brand-400'
            : 'bg-surface-800 border border-surface-700 text-surface-400 hover:text-surface-200 hover:border-surface-600'
        ]"
      >
        ⌨️ Atalhos
      </button>
    </div>

    <!-- Keyboard Shortcuts Panel -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="showShortcuts"
        class="card p-4 bg-surface-800/80 border-brand-500/20"
      >
        <div class="flex items-center gap-2 mb-3">
          <span class="text-sm font-semibold text-surface-200"
            >⌨️ Atalhos de Teclado</span
          >
          <span class="text-xs text-surface-500"
            >(mantenha o foco na página)</span
          >
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div class="flex items-center gap-2">
            <kbd class="kbd">V</kbd>
            <span class="text-surface-400">Trocar visualização</span>
          </div>
          <div class="flex items-center gap-2">
            <kbd class="kbd">M</kbd>
            <span class="text-surface-400">Trocar qualidade</span>
          </div>
          <div class="flex items-center gap-2">
            <kbd class="kbd">S</kbd>
            <span class="text-surface-400">Salvar captura</span>
          </div>
          <div class="flex items-center gap-2">
            <kbd class="kbd">H</kbd>
            <span class="text-surface-400">Mostrar/ocultar atalhos</span>
          </div>
        </div>
      </div>
    </Transition>

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
      <button
        @click="error = null"
        class="p-1.5 rounded-lg hover:bg-red-500/10 text-red-400"
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Left Column: Controls -->
      <div class="lg:col-span-1 space-y-4">
        <!-- Camera Selection -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">📹 Câmera</h3>

          <select
            v-model="selectedCamera"
            class="select mb-3"
            :disabled="isStreaming"
          >
            <option v-if="cameras.length === 0" value="">
              Nenhuma câmera encontrada
            </option>
            <option v-for="cam in cameras" :key="cam.id" :value="cam.id">
              {{ cam.label }}
            </option>
          </select>

          <div class="flex gap-2">
            <button
              v-if="!isStreaming"
              @click="startWebcam"
              :disabled="cameras.length === 0"
              class="btn-primary flex-1"
            >
              ▶️ Iniciar
            </button>
            <button v-else @click="stopWebcam" class="btn-danger flex-1">
              ⏹️ Parar
            </button>

            <button
              @click="listCameras"
              class="btn-secondary shrink-0"
              :disabled="isStreaming"
              title="Atualizar lista de câmeras"
            >
              🔄
            </button>
          </div>
        </div>

        <!-- Connection Status -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">📡 Status</h3>

          <div class="space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-400">Webcam</span>
              <span :class="isStreaming ? 'badge-green' : 'badge-surface'">
                {{ isStreaming ? 'Ativa' : 'Inativa' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-400">WebSocket</span>
              <span :class="isConnected ? 'badge-green' : 'badge-red'">
                {{ isConnected ? 'Conectado' : 'Desconectado' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-400">FPS (resposta)</span>
              <span class="text-xs font-mono text-surface-200">{{
                stats.fps
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-400">FPS (servidor)</span>
              <span class="text-xs font-mono text-surface-200">{{
                stats.serverFps
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-400">Latência</span>
              <span class="text-xs font-mono text-surface-200"
                >{{ stats.processingTime.toFixed(0) }}ms</span
              >
            </div>
          </div>
        </div>

        <!-- Visual Mode -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-surface-200">
              👁️ Visualização
            </h3>
            <kbd class="kbd text-[10px]">V</kbd>
          </div>

          <div class="space-y-1.5">
            <button
              v-for="vm in WEBCAM_VISUAL_MODES"
              :key="vm.value"
              @click="updateVisualMode(vm.value)"
              :class="[
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-all duration-200',
                visualMode === vm.value
                  ? 'bg-purple-600/15 border border-purple-500/30 text-purple-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200'
              ]"
            >
              <span class="text-sm shrink-0">{{ vm.icon }}</span>
              <div class="flex-1 min-w-0">
                <span class="text-sm font-medium block">{{ vm.label }}</span>
                <span class="text-[11px] text-surface-500 block truncate">{{
                  vm.description
                }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- Quality Mode -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-surface-200">🎯 Qualidade</h3>
            <kbd class="kbd text-[10px]">M</kbd>
          </div>

          <div class="space-y-1.5">
            <button
              v-for="qm in WEBCAM_QUALITY_MODES"
              :key="qm.value"
              @click="updateQualityMode(qm.value)"
              :class="[
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-all duration-200',
                qualityMode === qm.value
                  ? 'bg-amber-600/15 border border-amber-500/30 text-amber-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200'
              ]"
            >
              <span class="text-sm shrink-0">{{ qm.icon }}</span>
              <div class="flex-1 min-w-0">
                <span class="text-sm font-medium block">{{ qm.label }}</span>
                <span class="text-[11px] text-surface-500 block truncate">{{
                  qm.description
                }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- Detection Method -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">🔍 Método</h3>

          <div class="space-y-1.5">
            <button
              v-for="m in GRASS_METHODS.filter(m => m.value !== 'deeplearning')"
              :key="m.value"
              @click="updateMethod(m.value)"
              :class="[
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-all duration-200',
                method === m.value
                  ? 'bg-brand-600/15 border border-brand-500/30 text-brand-400'
                  : 'border border-transparent text-surface-400 hover:bg-surface-700/40 hover:text-surface-200'
              ]"
            >
              <span class="text-sm shrink-0">{{ m.icon }}</span>
              <span class="text-sm font-medium">{{ m.label }}</span>
            </button>
          </div>
        </div>

        <!-- Frame Rate -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">
            ⚡ Velocidade de Envio
          </h3>

          <div class="space-y-2">
            <input
              type="range"
              :value="frameInterval"
              @input="updateFrameRate(Number($event.target.value))"
              min="50"
              max="1000"
              step="50"
              class="w-full accent-brand-500"
            />
            <div
              class="flex items-center justify-between text-[11px] text-surface-500"
            >
              <span>Rápido (50ms)</span>
              <span class="font-mono text-surface-300"
                >{{ frameInterval }}ms</span
              >
              <span>Lento (1s)</span>
            </div>
          </div>
        </div>

        <!-- Display Options -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">
            🎨 Exibição
          </h3>

          <label class="flex items-center gap-3 cursor-pointer">
            <div
              :class="[
                'relative w-10 h-5 rounded-full transition-colors duration-200',
                showOverlay ? 'bg-brand-600' : 'bg-surface-600'
              ]"
              @click="showOverlay = !showOverlay"
            >
              <div
                :class="[
                  'absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200',
                  showOverlay ? 'translate-x-5' : 'translate-x-0.5'
                ]"
              />
            </div>
            <span class="text-sm text-surface-300">
              {{ showOverlay ? 'Mostrar Overlay' : 'Mostrar Original' }}
            </span>
          </label>
        </div>

        <!-- Snapshot -->
        <button
          @click="takeSnapshot"
          :disabled="!resultImage"
          class="btn-secondary w-full"
        >
          📸 Salvar Captura <kbd class="kbd ml-1 text-[10px]">S</kbd>
        </button>
      </div>

      <!-- Right Column: Video Feed + Stats -->
      <div class="lg:col-span-3 space-y-4">
        <!-- Video Display -->
        <div class="card overflow-hidden">
          <!-- Video Header Bar -->
          <div
            class="flex items-center justify-between px-4 py-2.5 border-b border-surface-700/50 bg-surface-800/40"
          >
            <div class="flex items-center gap-3">
              <div
                :class="[
                  'w-2.5 h-2.5 rounded-full',
                  isStreaming && isConnected
                    ? 'bg-red-500 animate-pulse'
                    : 'bg-surface-600'
                ]"
              />
              <span class="text-sm font-medium text-surface-300">
                {{ isStreaming ? 'AO VIVO' : 'Câmera desligada' }}
              </span>
            </div>

            <!-- Current mode badges -->
            <div v-if="isStreaming" class="flex items-center gap-2 text-xs">
              <span
                class="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 cursor-pointer hover:bg-purple-500/20 transition-colors"
                @click="cycleVisualMode"
                title="Clique ou pressione V para trocar"
              >
                {{ selectedVisualLabel }}
              </span>
              <span
                class="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 cursor-pointer hover:bg-amber-500/20 transition-colors"
                @click="toggleQualityMode"
                title="Clique ou pressione M para trocar"
              >
                {{ selectedQualityLabel }}
              </span>
              <span class="text-surface-500">{{ selectedMethodLabel }}</span>
              <span class="font-mono text-surface-400"
                >{{ stats.fps }} FPS</span
              >
            </div>
          </div>

          <!-- Video Content -->
          <div
            class="relative bg-surface-900 aspect-video flex items-center justify-center"
          >
            <!-- Hidden video element for capture -->
            <video
              ref="videoRef"
              class="absolute inset-0 w-full h-full object-contain"
              :class="{ 'opacity-0': showOverlay && resultImage }"
              autoplay
              playsinline
              muted
            />

            <!-- Canvas for frame capture (hidden) -->
            <canvas ref="canvasRef" class="hidden" />

            <!-- Overlay result image -->
            <img
              v-if="showOverlay && resultImage && isStreaming"
              :src="resultImage"
              alt="Processed frame"
              class="absolute inset-0 w-full h-full object-contain"
            />

            <!-- Empty state -->
            <div
              v-if="!isStreaming"
              class="flex flex-col items-center justify-center text-center z-10 p-8"
            >
              <div class="text-5xl mb-4">📹</div>
              <h3 class="text-lg font-semibold text-surface-300">
                Câmera Inativa
              </h3>
              <p class="text-sm text-surface-500 mt-1 max-w-sm">
                Selecione uma câmera e clique em "Iniciar" para começar a
                análise em tempo real.
              </p>
              <button
                @click="startWebcam"
                :disabled="cameras.length === 0"
                class="btn-primary mt-4"
              >
                ▶️ Iniciar Webcam
              </button>
            </div>

            <!-- Connecting overlay -->
            <div
              v-if="isStreaming && !isConnected"
              class="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center z-20"
            >
              <div
                class="w-12 h-12 rounded-full border-4 border-surface-700 border-t-brand-500 animate-spin"
              />
              <p class="text-sm text-surface-300 mt-4">
                Conectando ao servidor...
              </p>
            </div>

            <!-- Live stats overlay (bottom) -->
            <div
              v-if="isStreaming && isConnected"
              class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-4 py-3 z-10"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <span :class="['text-sm font-bold', coverageColor]">
                    Cobertura: {{ stats.coverage.toFixed(1) }}%
                  </span>
                  <span class="text-xs text-surface-400">
                    {{ stats.regions }} regiões
                  </span>
                </div>
                <div class="flex items-center gap-3">
                  <!-- Clickable visual mode toggle -->
                  <button
                    @click="cycleVisualMode"
                    class="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 transition-colors bg-purple-500/10 px-2 py-1 rounded-md"
                    title="Trocar visualização (V)"
                  >
                    👁️ {{ selectedVisualLabel }}
                  </button>
                  <span class="text-xs text-surface-500">
                    {{ stats.processingTime.toFixed(0) }}ms
                  </span>
                  <span class="text-xs font-mono text-surface-400">
                    {{ stats.fps }} FPS
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Live Stats Row -->
        <div v-if="isStreaming" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="stat-card animate-in stagger-1">
            <div class="flex items-center gap-2 mb-1">
              <div
                class="w-6 h-6 rounded-md bg-brand-500/10 flex items-center justify-center text-xs"
              >
                🌿
              </div>
              <span class="stat-label">Cobertura</span>
            </div>
            <span :class="['stat-value', coverageColor]">
              {{ stats.coverage.toFixed(1) }}%
            </span>
            <div class="mt-2">
              <div class="progress-bar h-1.5">
                <div
                  :class="['progress-fill', coverageBarColor]"
                  :style="{ width: `${Math.min(stats.coverage, 100)}%` }"
                />
              </div>
            </div>
            <span
              :class="[
                'mt-1.5 self-start text-[10px] font-semibold px-1.5 py-0.5 rounded',
                stats.coverage >= 60
                  ? 'bg-red-500/10 text-red-400'
                  : stats.coverage >= 30
                    ? 'bg-orange-500/10 text-orange-400'
                    : stats.coverage >= 10
                      ? 'bg-yellow-500/10 text-yellow-400'
                      : 'bg-brand-500/10 text-brand-400'
              ]"
            >
              {{ coverageLabel }}
            </span>
          </div>

          <div class="stat-card animate-in stagger-2">
            <div class="flex items-center gap-2 mb-1">
              <div
                class="w-6 h-6 rounded-md bg-blue-500/10 flex items-center justify-center text-xs"
              >
                🎯
              </div>
              <span class="stat-label">Regiões</span>
            </div>
            <span class="stat-value text-blue-400">{{ stats.regions }}</span>
            <span class="text-[11px] text-surface-500 mt-1">detectadas</span>
          </div>

          <div class="stat-card animate-in stagger-3">
            <div class="flex items-center gap-2 mb-1">
              <div
                class="w-6 h-6 rounded-md bg-purple-500/10 flex items-center justify-center text-xs"
              >
                ⚡
              </div>
              <span class="stat-label">Latência</span>
            </div>
            <span
              :class="[
                'stat-value',
                stats.processingTime > 500
                  ? 'text-red-400'
                  : stats.processingTime > 200
                    ? 'text-yellow-400'
                    : 'text-purple-400'
              ]"
            >
              {{ stats.processingTime.toFixed(0) }}
            </span>
            <span class="text-[11px] text-surface-500 mt-1">ms</span>
          </div>

          <div class="stat-card animate-in stagger-4">
            <div class="flex items-center gap-2 mb-1">
              <div
                class="w-6 h-6 rounded-md bg-amber-500/10 flex items-center justify-center text-xs"
              >
                🎞️
              </div>
              <span class="stat-label">FPS</span>
            </div>
            <span
              :class="[
                'stat-value',
                stats.fps < 3
                  ? 'text-red-400'
                  : stats.fps < 8
                    ? 'text-yellow-400'
                    : 'text-amber-400'
              ]"
            >
              {{ stats.fps }}
            </span>
            <span class="text-[11px] text-surface-500 mt-1">frames/s</span>
          </div>
        </div>

        <!-- Active Configuration Summary -->
        <div v-if="isStreaming && isConnected" class="card p-4">
          <div
            class="flex items-center gap-3 flex-wrap text-xs text-surface-500"
          >
            <span class="font-medium text-surface-400">🎮 Config ativa:</span>
            <span
              class="px-2 py-0.5 rounded bg-surface-700/50 text-surface-300"
            >
              {{ selectedMethodLabel }}
            </span>
            <span class="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">
              👁️ {{ selectedVisualLabel }}
            </span>
            <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400">
              🎯 {{ selectedQualityLabel }}
            </span>
            <span class="text-surface-600">•</span>
            <span>
              <kbd class="kbd text-[10px]">V</kbd> visualização
              <kbd class="kbd text-[10px] ml-1">M</kbd> qualidade
              <kbd class="kbd text-[10px] ml-1">S</kbd> salvar
              <kbd class="kbd text-[10px] ml-1">H</kbd> ajuda
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kbd {
  @apply inline-flex items-center justify-center px-1.5 py-0.5 rounded border text-[11px] font-mono font-semibold;
  @apply bg-surface-700/50 border-surface-600 text-surface-300;
}
</style>
