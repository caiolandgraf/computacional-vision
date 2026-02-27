<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

// ── Tab control ─────────────────────────────────────────────────────────────
const activeTab = ref('webcam') // 'webcam' | 'image' | 'video'

// ── Shared options ───────────────────────────────────────────────────────────
const blurFaces = ref(false)
const quality = ref('1') // '1' = tempo real, '2' = alta precisão

// ═══════════════════════════════════════════════════════════════════════════
//  WEBCAM
// ═══════════════════════════════════════════════════════════════════════════
const videoRef = ref(null)
const canvasRef = ref(null)
const isStreaming = ref(false)
const isConnected = ref(false)
const webcamError = ref('')
const resultImage = ref('')
const showOverlay = ref(true)
const frameInterval = ref(33) // ms entre frames (~30 FPS)

const webcamStats = ref({
  person_count: 0,
  face_count: 0,
  body_count: 0,
  blur_applied: false,
  processing_time_ms: 0,
  fps: 0,
  recv_fps: 0,
  method: '—'
})

let socket = null
let stream = null
let sendTimer = null
let fpsCounter = 0
let fpsTimer = null
let clientFps = ref(0)

const cameras = ref([])
const selectedCamera = ref('')

async function listCameras() {
  try {
    // Solicita permissão primeiro para que os labels apareçam
    await navigator.mediaDevices
      .getUserMedia({ video: true })
      .then(s => s.getTracks().forEach(t => t.stop()))
      .catch(() => {})

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
  webcamError.value = ''
  try {
    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 }
      }
    }
    if (selectedCamera.value) {
      constraints.video.deviceId = { exact: selectedCamera.value }
    }

    stream = await navigator.mediaDevices.getUserMedia(constraints)
    videoRef.value.srcObject = stream
    await videoRef.value.play()
    isStreaming.value = true
    connectWebSocket()
  } catch (err) {
    if (err.name === 'NotAllowedError') {
      webcamError.value =
        'Permissão de câmera negada. Verifique as permissões do navegador.'
    } else if (err.name === 'NotFoundError') {
      webcamError.value = 'Câmera não encontrada. Verifique se está conectada.'
    } else if (err.name === 'OverconstrainedError') {
      webcamError.value =
        'A câmera selecionada não está disponível. Tente outra.'
    } else {
      webcamError.value = `Erro ao acessar webcam: ${err.message}`
    }
  }
}

function stopWebcam() {
  clearInterval(sendTimer)
  clearInterval(fpsTimer)
  sendTimer = null

  if (socket) {
    socket.close()
    socket = null
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (videoRef.value) videoRef.value.srcObject = null

  isStreaming.value = false
  isConnected.value = false
  resultImage.value = ''
  clientFps.value = 0
  webcamStats.value = {
    person_count: 0,
    face_count: 0,
    body_count: 0,
    blur_applied: false,
    processing_time_ms: 0,
    fps: 0,
    recv_fps: 0,
    method: '—'
  }
}

function connectWebSocket() {
  const wsProto = location.protocol === 'https:' ? 'wss' : 'ws'
  const wsHost = import.meta.env.VITE_API_URL
    ? import.meta.env.VITE_API_URL.replace(/^https?/, wsProto)
    : `${wsProto}://${location.hostname}:8000`

  socket = new WebSocket(`${wsHost}/api/ws/people-webcam`)

  socket.onopen = () => {
    isConnected.value = true
    sendConfig()
    startSendingFrames()
    fpsTimer = setInterval(() => {
      clientFps.value = fpsCounter
      fpsCounter = 0
    }, 1000)
  }

  socket.onmessage = evt => {
    const msg = JSON.parse(evt.data)
    if (msg.type === 'result') {
      if (showOverlay.value)
        resultImage.value = `data:image/jpeg;base64,${msg.image}`
      webcamStats.value = msg.stats
    }
  }

  socket.onerror = () => {
    webcamError.value = 'Erro na conexão WebSocket com o servidor.'
    stopWebcam()
  }

  socket.onclose = () => {
    isConnected.value = false
  }
}

function sendConfig() {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(
      JSON.stringify({
        type: 'config',
        blur_faces: blurFaces.value,
        quality: quality.value
      })
    )
  }
}

function startSendingFrames() {
  clearInterval(sendTimer)
  sendTimer = setInterval(() => {
    if (
      !videoRef.value ||
      !canvasRef.value ||
      socket?.readyState !== WebSocket.OPEN
    )
      return
    const video = videoRef.value
    const canvas = canvasRef.value
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.55)
    const base64 = dataUrl.split(',')[1]
    socket.send(JSON.stringify({ type: 'frame', data: base64 }))
    fpsCounter++
  }, frameInterval.value)
}

watch(blurFaces, sendConfig)
watch(quality, sendConfig)
watch(frameInterval, () => {
  if (isStreaming.value) startSendingFrames()
})

onMounted(() => {
  listCameras()
})

// ═══════════════════════════════════════════════════════════════════════════
//  IMAGE UPLOAD
// ═══════════════════════════════════════════════════════════════════════════
const imgFile = ref(null)
const imgPreview = ref('')
const imgResult = ref('')
const imgStats = ref(null)
const imgLoading = ref(false)
const imgError = ref('')
const imgDragOver = ref(false)
const imgInputRef = ref(null)

function onImgFileChange(evt) {
  const f = evt.target.files[0]
  if (f) setImgFile(f)
}

function setImgFile(f) {
  const valid = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
  const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase()
  if (!valid.includes(ext)) {
    imgError.value = `Formato inválido. Use: ${valid.join(', ')}`
    return
  }
  imgFile.value = f
  imgError.value = ''
  imgResult.value = ''
  imgStats.value = null
  const reader = new FileReader()
  reader.onload = e => {
    imgPreview.value = e.target.result
  }
  reader.readAsDataURL(f)
}

function onImgDrop(evt) {
  imgDragOver.value = false
  const f = evt.dataTransfer.files[0]
  if (f) setImgFile(f)
}

function clearImg() {
  imgFile.value = null
  imgPreview.value = ''
  imgResult.value = ''
  imgStats.value = null
  imgError.value = ''
  if (imgInputRef.value) imgInputRef.value.value = ''
}

async function analyzeImage() {
  if (!imgFile.value) return
  imgLoading.value = true
  imgError.value = ''
  imgResult.value = ''
  imgStats.value = null

  try {
    const form = new FormData()
    form.append('file', imgFile.value)
    form.append('blur_faces', String(blurFaces.value))

    const baseUrl = import.meta.env.VITE_API_URL || ''
    const res = await fetch(`${baseUrl}/api/people/analyze`, {
      method: 'POST',
      body: form
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    const data = await res.json()
    imgResult.value = `data:image/jpeg;base64,${data.image}`
    imgStats.value = data.stats
  } catch (err) {
    imgError.value = `Erro: ${err.message}`
  } finally {
    imgLoading.value = false
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  VIDEO UPLOAD
// ═══════════════════════════════════════════════════════════════════════════
const vidFile = ref(null)
const vidDragOver = ref(false)
const vidInputRef = ref(null)
const vidLoading = ref(false)
const vidError = ref('')
const vidJobId = ref(null)
const vidJob = ref(null)
const vidCompleted = ref(false)
let vidPollTimer = null

const vidProgress = computed(() => vidJob.value?.progress ?? 0)
const vidEta = computed(() => {
  const s = vidJob.value?.eta_seconds ?? 0
  if (!s) return '--'
  const m = Math.floor(s / 60)
  const sec = Math.round(s % 60)
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`
})
const vidIsProcessing = computed(
  () =>
    vidJob.value?.status === 'queued' || vidJob.value?.status === 'processing'
)

function onVidFileChange(evt) {
  const f = evt.target.files[0]
  if (f) setVidFile(f)
}

function setVidFile(f) {
  const valid = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
  const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase()
  if (!valid.includes(ext)) {
    vidError.value = `Formato inválido. Use: ${valid.join(', ')}`
    return
  }
  vidFile.value = f
  vidError.value = ''
  vidJobId.value = null
  vidJob.value = null
  vidCompleted.value = false
}

function onVidDrop(evt) {
  vidDragOver.value = false
  const f = evt.dataTransfer.files[0]
  if (f) setVidFile(f)
}

function clearVid() {
  clearInterval(vidPollTimer)
  vidFile.value = null
  vidJobId.value = null
  vidJob.value = null
  vidCompleted.value = false
  vidError.value = ''
  if (vidInputRef.value) vidInputRef.value.value = ''
}

async function startVideoProcessing() {
  if (!vidFile.value) return
  vidLoading.value = true
  vidError.value = ''
  vidCompleted.value = false
  vidJob.value = null

  try {
    const form = new FormData()
    form.append('file', vidFile.value)
    form.append('blur_faces', String(blurFaces.value))

    const baseUrl = import.meta.env.VITE_API_URL || ''
    const res = await fetch(`${baseUrl}/api/people/video/process`, {
      method: 'POST',
      body: form
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    const data = await res.json()
    vidJobId.value = data.job_id
    vidJob.value = { status: 'queued', progress: 0 }

    // Polling
    vidPollTimer = setInterval(async () => {
      try {
        const sr = await fetch(
          `${baseUrl}/api/people/video/status/${vidJobId.value}`
        )
        const job = await sr.json()
        vidJob.value = job
        if (job.status === 'completed') {
          clearInterval(vidPollTimer)
          vidCompleted.value = true
        } else if (job.status === 'error') {
          clearInterval(vidPollTimer)
          vidError.value = job.error || 'Erro ao processar vídeo.'
        }
      } catch {
        /* silently ignore poll errors */
      }
    }, 1500)
  } catch (err) {
    vidError.value = `Erro: ${err.message}`
  } finally {
    vidLoading.value = false
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function getJobStatusBadge(status) {
  const map = {
    queued: {
      cls: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      icon: '⏳',
      label: 'Na fila'
    },
    processing: {
      cls: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      icon: '⚙️',
      label: 'Processando'
    },
    completed: {
      cls: 'bg-green-500/20 text-green-400 border-green-500/30',
      icon: '✅',
      label: 'Concluído'
    },
    error: {
      cls: 'bg-red-500/20 text-red-400 border-red-500/30',
      icon: '❌',
      label: 'Erro'
    }
  }
  return map[status] || map.queued
}

// ── Cleanup ──────────────────────────────────────────────────────────────────
onUnmounted(() => {
  stopWebcam()
  clearInterval(vidPollTimer)
})
</script>

<template>
  <div class="space-y-6">
    <!-- ── Page header ──────────────────────────────────────────────────── -->
    <div
      class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
    >
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-2">
          <span>🧑‍🤝‍🧑</span> Detecção de Pessoas
        </h1>
        <p class="text-surface-400 mt-1 text-sm">
          Conta pessoas, detecta rostos e oferece anonimização via desfoque em
          imagens, vídeos e webcam em tempo real.
        </p>
      </div>
    </div>

    <!-- ── Global options bar ────────────────────────────────────────────── -->
    <div
      class="bg-surface-800/60 border border-surface-700/50 rounded-2xl p-4 flex flex-wrap gap-4 items-center"
    >
      <!-- Blur toggle -->
      <label class="flex items-center gap-3 cursor-pointer select-none group">
        <div
          :class="[
            'relative w-11 h-6 rounded-full transition-colors duration-300',
            blurFaces ? 'bg-brand-600' : 'bg-surface-600'
          ]"
          @click="blurFaces = !blurFaces"
        >
          <div
            :class="[
              'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-300',
              blurFaces ? 'translate-x-5' : 'translate-x-0'
            ]"
          />
        </div>
        <span
          class="text-sm font-medium text-surface-200 group-hover:text-white transition-colors"
        >
          {{
            blurFaces
              ? '🙈 Blur de rostos ativo'
              : '👁️ Blur de rostos desativado'
          }}
        </span>
      </label>

      <div class="w-px h-6 bg-surface-700 hidden sm:block" />

      <!-- Quality selector -->
      <div class="flex items-center gap-2">
        <span
          class="text-xs text-surface-400 font-medium uppercase tracking-wide"
          >Qualidade</span
        >
        <div class="flex rounded-xl overflow-hidden border border-surface-700">
          <button
            v-for="opt in [
              { v: '1', label: 'Tempo Real', icon: '⚡' },
              { v: '2', label: 'Alta Precisão', icon: '🔬' }
            ]"
            :key="opt.v"
            @click="quality = opt.v"
            :class="[
              'px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5',
              quality === opt.v
                ? 'bg-brand-600 text-white'
                : 'text-surface-400 hover:text-white hover:bg-surface-700'
            ]"
          >
            <span>{{ opt.icon }}</span>
            <span class="hidden sm:inline">{{ opt.label }}</span>
          </button>
        </div>
      </div>

      <div
        class="ml-auto text-xs text-surface-500 hidden lg:flex items-center gap-1.5"
      >
        <span class="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
        HOG + Haar Cascade
      </div>
    </div>

    <!-- ── Tabs ──────────────────────────────────────────────────────────── -->
    <div
      class="flex gap-1 bg-surface-800/40 p-1 rounded-2xl border border-surface-700/40 w-fit"
    >
      <button
        v-for="tab in [
          { id: 'webcam', icon: '📹', label: 'Webcam' },
          { id: 'image', icon: '🖼️', label: 'Imagem' },
          { id: 'video', icon: '🎬', label: 'Vídeo' }
        ]"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200',
          activeTab === tab.id
            ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
            : 'text-surface-400 hover:text-white hover:bg-surface-700/60'
        ]"
      >
        <span>{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════
         TAB: WEBCAM
         ════════════════════════════════════════════════════════════════════ -->
    <div
      v-if="activeTab === 'webcam'"
      class="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-6"
    >
      <!-- Video panel -->
      <div
        class="bg-surface-800/60 border border-surface-700/50 rounded-2xl overflow-hidden flex flex-col"
      >
        <!-- Header -->
        <div
          class="flex items-center justify-between px-5 py-3.5 border-b border-surface-700/40"
        >
          <div class="flex items-center gap-2.5">
            <div
              :class="[
                'w-2.5 h-2.5 rounded-full transition-colors',
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-surface-600'
              ]"
            />
            <span class="text-sm font-semibold text-surface-200">
              {{
                isStreaming
                  ? isConnected
                    ? 'Ao vivo'
                    : 'Conectando...'
                  : 'Câmera desligada'
              }}
            </span>
          </div>
          <div
            v-if="isStreaming"
            class="flex items-center gap-3 text-xs text-surface-400"
          >
            <span
              :class="[
                'font-mono font-semibold',
                webcamStats.fps >= 25
                  ? 'text-green-400'
                  : webcamStats.fps >= 15
                    ? 'text-yellow-400'
                    : 'text-red-400'
              ]"
              >{{ webcamStats.fps || clientFps }} fps</span
            >
            <span v-if="webcamStats.processing_time_ms" class="text-surface-500"
              >{{ webcamStats.processing_time_ms }}ms</span
            >
          </div>
        </div>

        <!-- Video area -->
        <div
          class="relative bg-black flex-1 min-h-[320px] flex items-center justify-center"
        >
          <!-- Raw feed -->
          <video
            ref="videoRef"
            autoplay
            playsinline
            muted
            :class="[
              'w-full h-full object-contain transition-opacity duration-300',
              resultImage && showOverlay ? 'opacity-0 absolute' : 'opacity-100'
            ]"
            style="max-height: 520px"
          />
          <!-- Processed overlay -->
          <canvas ref="canvasRef" class="hidden" />
          <img
            v-if="resultImage && showOverlay"
            :src="resultImage"
            alt="resultado"
            class="w-full h-full object-contain"
            style="max-height: 520px"
          />

          <!-- Idle placeholder -->
          <div
            v-if="!isStreaming"
            class="flex flex-col items-center gap-3 text-surface-500 p-8 text-center"
          >
            <span class="text-5xl">📷</span>
            <p class="text-base font-medium text-surface-400">
              Webcam desligada
            </p>
            <p class="text-sm">
              Clique em
              <strong class="text-brand-400">Iniciar Câmera</strong> para
              começar
            </p>
          </div>

          <!-- Error overlay -->
          <div
            v-if="webcamError"
            class="absolute inset-0 flex items-center justify-center bg-surface-900/90"
          >
            <div class="text-center p-6">
              <span class="text-4xl">⚠️</span>
              <p class="text-red-400 mt-3 text-sm max-w-xs">
                {{ webcamError }}
              </p>
            </div>
          </div>

          <!-- Person count badge (live) -->
          <div
            v-if="isConnected && webcamStats.person_count !== undefined"
            class="absolute top-3 right-3 bg-black/70 backdrop-blur-sm border border-brand-500/40 rounded-xl px-3 py-1.5 flex items-center gap-2"
          >
            <span class="text-2xl font-bold text-brand-400">{{
              webcamStats.person_count
            }}</span>
            <span class="text-xs text-surface-300"
              >pessoa{{ webcamStats.person_count !== 1 ? 's' : '' }}</span
            >
          </div>

          <!-- Blur badge -->
          <div
            v-if="blurFaces && isConnected"
            class="absolute top-3 left-3 bg-purple-600/80 backdrop-blur-sm rounded-xl px-2.5 py-1 text-xs font-semibold text-white flex items-center gap-1"
          >
            🙈 BLUR ATIVO
          </div>
        </div>

        <!-- Controls -->
        <div class="flex flex-col gap-3 p-4 border-t border-surface-700/40">
          <!-- Camera selector row -->
          <div v-if="!isStreaming" class="flex items-center gap-2">
            <select
              v-model="selectedCamera"
              class="flex-1 bg-surface-700/60 border border-surface-600/60 text-surface-200 text-sm rounded-xl px-3 py-2 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/40 transition-colors"
              :disabled="cameras.length === 0"
            >
              <option v-if="cameras.length === 0" value="">
                Nenhuma câmera detectada
              </option>
              <option v-for="cam in cameras" :key="cam.id" :value="cam.id">
                {{ cam.label }}
              </option>
            </select>
            <button
              @click="listCameras"
              title="Atualizar lista de câmeras"
              class="shrink-0 p-2 rounded-xl bg-surface-700/60 border border-surface-600/60 text-surface-400 hover:text-white hover:bg-surface-700 hover:border-surface-500 transition-colors text-sm"
            >
              🔄
            </button>
          </div>

          <!-- Current camera indicator when streaming -->
          <div
            v-if="isStreaming && selectedCamera"
            class="flex items-center gap-2 text-xs text-surface-400"
          >
            <span
              class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shrink-0"
            ></span>
            <span class="truncate">
              {{
                cameras.find(c => c.id === selectedCamera)?.label ??
                'Câmera ativa'
              }}
            </span>
          </div>

          <!-- Start / Stop row -->
          <div class="flex items-center gap-3 flex-wrap">
            <button
              v-if="!isStreaming"
              @click="startWebcam"
              :disabled="cameras.length === 0"
              :class="[
                'flex items-center gap-2 px-5 py-2.5 font-semibold rounded-xl transition-colors text-sm',
                cameras.length === 0
                  ? 'bg-surface-700 text-surface-500 cursor-not-allowed'
                  : 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20'
              ]"
            >
              <span>▶</span> Iniciar Câmera
            </button>
            <button
              v-else
              @click="stopWebcam"
              class="flex items-center gap-2 px-5 py-2.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 font-semibold rounded-xl transition-colors text-sm"
            >
              <span>⏹</span> Parar
            </button>

            <label
              v-if="isStreaming"
              class="flex items-center gap-2 cursor-pointer ml-2"
            >
              <input type="checkbox" v-model="showOverlay" class="sr-only" />
              <div
                :class="[
                  'w-8 h-4 rounded-full transition-colors',
                  showOverlay ? 'bg-brand-600' : 'bg-surface-600'
                ]"
              >
                <div
                  :class="[
                    'w-3.5 h-3.5 m-0.5 rounded-full bg-white transition-transform',
                    showOverlay ? 'translate-x-4' : 'translate-x-0'
                  ]"
                />
              </div>
              <span class="text-xs text-surface-400">Overlay</span>
            </label>

            <div
              v-if="isStreaming"
              class="ml-auto flex items-center gap-2 text-xs text-surface-400"
            >
              <label for="frame-rate" class="whitespace-nowrap"
                >Intervalo (ms)</label
              >
              <input
                id="frame-rate"
                type="range"
                v-model.number="frameInterval"
                min="100"
                max="1000"
                step="50"
                class="w-24 accent-brand-500"
              />
              <span class="w-10 text-right text-surface-300">{{
                frameInterval
              }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats panel -->
      <div class="flex flex-col gap-4">
        <!-- Count cards -->
        <div class="grid grid-cols-3 gap-3">
          <div
            v-for="stat in [
              {
                label: 'Pessoas',
                value: webcamStats.person_count,
                icon: '🧑‍🤝‍🧑',
                color: 'text-brand-400'
              },
              {
                label: 'Rostos',
                value: webcamStats.face_count,
                icon: '😊',
                color: 'text-green-400'
              },
              {
                label: 'Corpos',
                value: webcamStats.body_count,
                icon: '🧍',
                color: 'text-yellow-400'
              }
            ]"
            :key="stat.label"
            class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-3 text-center"
          >
            <div class="text-xl mb-1">{{ stat.icon }}</div>
            <div :class="['text-2xl font-bold', stat.color]">
              {{ stat.value ?? 0 }}
            </div>
            <div
              class="text-[10px] text-surface-500 mt-0.5 uppercase tracking-wide"
            >
              {{ stat.label }}
            </div>
          </div>
        </div>

        <!-- Timing -->
        <div
          class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-4 space-y-3"
        >
          <h3
            class="text-xs font-semibold text-surface-400 uppercase tracking-wide"
          >
            Performance
          </h3>
          <div
            v-for="row in [
              { label: 'FPS enviado', value: clientFps + ' fps' },
              {
                label: 'FPS recebido',
                value: (webcamStats.recv_fps || 0) + ' fps'
              },
              {
                label: 'FPS resultado',
                value: (webcamStats.fps || 0) + ' fps'
              },
              {
                label: 'Tempo processo',
                value: (webcamStats.processing_time_ms || 0) + ' ms'
              }
            ]"
            :key="row.label"
            class="flex justify-between items-center"
          >
            <span class="text-xs text-surface-400">{{ row.label }}</span>
            <span class="text-sm font-semibold text-surface-200">{{
              row.value
            }}</span>
          </div>
        </div>

        <!-- Blur info card -->
        <div
          :class="[
            'rounded-xl p-4 border transition-colors',
            blurFaces
              ? 'bg-purple-600/10 border-purple-500/30'
              : 'bg-surface-800/40 border-surface-700/30'
          ]"
        >
          <div class="flex items-start gap-3">
            <span class="text-2xl">{{ blurFaces ? '🙈' : '👁️' }}</span>
            <div>
              <p class="text-sm font-semibold text-surface-200">
                {{ blurFaces ? 'Anonimização ativa' : 'Anonimização inativa' }}
              </p>
              <p class="text-xs text-surface-400 mt-0.5">
                {{
                  blurFaces
                    ? 'Os rostos detectados estão sendo desfocados para proteger a privacidade.'
                    : 'Ative o "Blur de rostos" para esconder as identidades.'
                }}
              </p>
            </div>
          </div>
        </div>

        <!-- Detector info -->
        <div
          class="bg-surface-800/40 border border-surface-700/30 rounded-xl p-4 space-y-2 text-xs text-surface-400"
        >
          <h3
            class="text-xs font-semibold text-surface-300 uppercase tracking-wide mb-2"
          >
            Detalhes do detector
          </h3>
          <div class="flex justify-between">
            <span>Método ativo</span>
            <span class="text-brand-400 font-mono font-semibold">{{
              webcamStats.method || '—'
            }}</span>
          </div>
          <div class="flex justify-between">
            <span>Corpo</span>
            <span class="text-surface-300">YOLO nano → HOG</span>
          </div>
          <div class="flex justify-between">
            <span>Rosto</span>
            <span class="text-surface-300">YuNet → Haar</span>
          </div>
          <div class="flex justify-between">
            <span>NMS</span><span class="text-surface-300">IoU 0.45</span>
          </div>
          <div class="flex justify-between">
            <span>Modo</span
            ><span class="text-surface-300">{{
              quality === '2' ? 'Alta precisão' : 'Tempo real'
            }}</span>
          </div>
          <div class="flex justify-between">
            <span>Resolução</span>
            <span class="text-surface-300">640 × 480</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════
         TAB: IMAGE
         ════════════════════════════════════════════════════════════════════ -->
    <div
      v-if="activeTab === 'image'"
      class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6"
    >
      <!-- Left: upload + result -->
      <div class="space-y-5">
        <!-- Drop zone -->
        <div
          v-if="!imgFile"
          @dragover.prevent="imgDragOver = true"
          @dragleave.prevent="imgDragOver = false"
          @drop.prevent="onImgDrop"
          @click="imgInputRef?.click()"
          :class="[
            'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors',
            imgDragOver
              ? 'border-brand-500 bg-brand-600/10'
              : 'border-surface-600 hover:border-surface-500 bg-surface-800/40 hover:bg-surface-800/70'
          ]"
        >
          <input
            ref="imgInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onImgFileChange"
          />
          <div class="flex flex-col items-center gap-3 text-surface-400">
            <span class="text-5xl">🖼️</span>
            <p class="text-base font-medium text-surface-300">
              Arraste uma imagem aqui
            </p>
            <p class="text-sm">ou clique para selecionar</p>
            <p class="text-xs text-surface-500">JPG, JPEG, PNG, BMP, WEBP</p>
          </div>
        </div>

        <!-- File selected -->
        <div
          v-if="imgFile"
          class="bg-surface-800/60 border border-surface-700/50 rounded-2xl overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-5 py-3 border-b border-surface-700/40"
          >
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-xl shrink-0">🖼️</span>
              <div class="min-w-0">
                <p class="text-sm font-medium text-surface-200 truncate">
                  {{ imgFile.name }}
                </p>
                <p class="text-xs text-surface-500">
                  {{ formatFileSize(imgFile.size) }}
                </p>
              </div>
            </div>
            <button
              @click="clearImg"
              class="text-surface-500 hover:text-red-400 transition-colors ml-3 shrink-0"
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

          <!-- Preview -->
          <div
            class="relative bg-black flex items-center justify-center"
            style="min-height: 200px; max-height: 480px"
          >
            <img
              v-if="imgResult"
              :src="imgResult"
              alt="resultado"
              class="w-full object-contain"
              style="max-height: 480px"
            />
            <img
              v-else-if="imgPreview"
              :src="imgPreview"
              alt="preview"
              class="w-full object-contain opacity-70"
              style="max-height: 480px"
            />
          </div>
        </div>

        <!-- Error -->
        <div
          v-if="imgError"
          class="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400 flex items-center gap-2"
        >
          <span>⚠️</span> {{ imgError }}
        </div>

        <!-- Analyze button -->
        <button
          v-if="imgFile"
          @click="analyzeImage"
          :disabled="imgLoading"
          :class="[
            'w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all',
            imgLoading
              ? 'bg-surface-700 text-surface-400 cursor-not-allowed'
              : 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20'
          ]"
        >
          <template v-if="imgLoading">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Analisando...
          </template>
          <template v-else> <span>🔍</span> Detectar Pessoas </template>
        </button>
      </div>

      <!-- Right: stats panel -->
      <div class="space-y-4">
        <!-- Result stats -->
        <div v-if="imgStats" class="space-y-4">
          <div class="grid grid-cols-3 gap-3">
            <div
              v-for="stat in [
                {
                  label: 'Pessoas',
                  value: imgStats.person_count,
                  icon: '🧑‍🤝‍🧑',
                  color: 'text-brand-400'
                },
                {
                  label: 'Rostos',
                  value: imgStats.face_count,
                  icon: '😊',
                  color: 'text-green-400'
                },
                {
                  label: 'Corpos',
                  value: imgStats.body_count,
                  icon: '🧍',
                  color: 'text-yellow-400'
                }
              ]"
              :key="stat.label"
              class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-3 text-center"
            >
              <div class="text-xl mb-1">{{ stat.icon }}</div>
              <div :class="['text-2xl font-bold', stat.color]">
                {{ stat.value ?? 0 }}
              </div>
              <div
                class="text-[10px] text-surface-500 mt-0.5 uppercase tracking-wide"
              >
                {{ stat.label }}
              </div>
            </div>
          </div>

          <div
            class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-4 space-y-2 text-sm"
          >
            <h3
              class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-3"
            >
              Detalhes
            </h3>
            <div class="flex justify-between">
              <span class="text-surface-400">Processamento</span>
              <span class="text-surface-200 font-medium"
                >{{ imgStats.processing_time_ms }} ms</span
              >
            </div>
            <div class="flex justify-between">
              <span class="text-surface-400">Dimensões</span>
              <span class="text-surface-200 font-medium"
                >{{ imgStats.image_width }}×{{ imgStats.image_height }}</span
              >
            </div>
            <div class="flex justify-between">
              <span class="text-surface-400">Blur aplicado</span>
              <span
                :class="
                  imgStats.blur_applied ? 'text-purple-400' : 'text-surface-400'
                "
              >
                {{ imgStats.blur_applied ? '✅ Sim' : '❌ Não' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-400">Método</span>
              <span class="text-surface-200 font-medium">{{
                imgStats.method
              }}</span>
            </div>
          </div>

          <!-- Faces list -->
          <div
            v-if="imgStats.faces?.length"
            class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-4"
          >
            <h3
              class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-3"
            >
              Rostos detectados
            </h3>
            <div class="space-y-1.5 max-h-48 overflow-y-auto">
              <div
                v-for="(face, i) in imgStats.faces"
                :key="i"
                class="flex items-center gap-2 text-xs text-surface-400 bg-surface-700/30 rounded-lg px-3 py-1.5"
              >
                <span class="text-green-400 font-bold">#{{ i + 1 }}</span>
                <span>{{ face.label }}</span>
                <span class="ml-auto text-surface-500"
                  >{{ face.w }}×{{ face.h }} px</span
                >
              </div>
            </div>
          </div>

          <!-- Bodies list -->
          <div
            v-if="imgStats.bodies?.length"
            class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-4"
          >
            <h3
              class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-3"
            >
              Corpos detectados (HOG)
            </h3>
            <div class="space-y-1.5 max-h-48 overflow-y-auto">
              <div
                v-for="(body, i) in imgStats.bodies"
                :key="i"
                class="flex items-center gap-2 text-xs text-surface-400 bg-surface-700/30 rounded-lg px-3 py-1.5"
              >
                <span class="text-brand-400 font-bold">#{{ i + 1 }}</span>
                <span>{{ body.label }}</span>
                <span class="ml-auto text-surface-500"
                  >conf: {{ body.confidence.toFixed(2) }}</span
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Placeholder before analysis -->
        <div
          v-else
          class="bg-surface-800/40 border border-surface-700/30 rounded-xl p-8 text-center space-y-3"
        >
          <span class="text-4xl">🔍</span>
          <p class="text-surface-400 text-sm">
            Selecione uma imagem e clique em<br /><strong class="text-brand-400"
              >Detectar Pessoas</strong
            >
          </p>
        </div>

        <!-- Algorithm info -->
        <div
          class="bg-surface-800/40 border border-surface-700/30 rounded-xl p-4 space-y-2 text-xs text-surface-400"
        >
          <h3
            class="text-xs font-semibold text-surface-300 uppercase tracking-wide mb-2"
          >
            Como funciona
          </h3>
          <p>
            1. <strong class="text-surface-300">YOLO nano</strong> detecta
            corpos inteiros (fallback: HOG+SVM).
          </p>
          <p>
            2. <strong class="text-surface-300">YuNet</strong> detecta rostos em
            múltiplos ângulos (fallback: Haar Cascade).
          </p>
          <p>
            3. <strong class="text-surface-300">NMS</strong> remove detecções
            duplicadas.
          </p>
          <p>4. Fusão inteligente evita dupla contagem de pessoas.</p>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════
         TAB: VIDEO
         ════════════════════════════════════════════════════════════════════ -->
    <div
      v-if="activeTab === 'video'"
      class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6"
    >
      <!-- Left: upload + progress -->
      <div class="space-y-5">
        <!-- Drop zone -->
        <div
          v-if="!vidFile"
          @dragover.prevent="vidDragOver = true"
          @dragleave.prevent="vidDragOver = false"
          @drop.prevent="onVidDrop"
          @click="vidInputRef?.click()"
          :class="[
            'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors',
            vidDragOver
              ? 'border-brand-500 bg-brand-600/10'
              : 'border-surface-600 hover:border-surface-500 bg-surface-800/40 hover:bg-surface-800/70'
          ]"
        >
          <input
            ref="vidInputRef"
            type="file"
            accept="video/*"
            class="hidden"
            @change="onVidFileChange"
          />
          <div class="flex flex-col items-center gap-3 text-surface-400">
            <span class="text-5xl">🎬</span>
            <p class="text-base font-medium text-surface-300">
              Arraste um vídeo aqui
            </p>
            <p class="text-sm">ou clique para selecionar</p>
            <p class="text-xs text-surface-500">MP4, AVI, MOV, MKV, WEBM</p>
          </div>
        </div>

        <!-- File card -->
        <div
          v-if="vidFile"
          class="bg-surface-800/60 border border-surface-700/50 rounded-2xl overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-5 py-3.5 border-b border-surface-700/40"
          >
            <div class="flex items-center gap-3 min-w-0">
              <span class="text-xl shrink-0">🎬</span>
              <div class="min-w-0">
                <p class="text-sm font-medium text-surface-200 truncate">
                  {{ vidFile.name }}
                </p>
                <p class="text-xs text-surface-500">
                  {{ formatFileSize(vidFile.size) }}
                </p>
              </div>
            </div>
            <button
              v-if="!vidIsProcessing"
              @click="clearVid"
              class="text-surface-500 hover:text-red-400 transition-colors ml-3 shrink-0"
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

          <!-- Progress -->
          <div v-if="vidJob" class="p-5 space-y-4">
            <!-- Status badge -->
            <div class="flex items-center gap-3">
              <span
                :class="[
                  'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border',
                  getJobStatusBadge(vidJob.status).cls
                ]"
              >
                {{ getJobStatusBadge(vidJob.status).icon }}
                {{ getJobStatusBadge(vidJob.status).label }}
              </span>
              <span v-if="vidIsProcessing" class="text-xs text-surface-400">
                Frame {{ vidJob.current_frame }} / {{ vidJob.total_frames }}
              </span>
            </div>

            <!-- Progress bar -->
            <div v-if="vidIsProcessing || vidCompleted">
              <div class="flex justify-between text-xs text-surface-400 mb-1.5">
                <span>Progresso</span>
                <span>{{ vidProgress.toFixed(1) }}%</span>
              </div>
              <div
                class="w-full bg-surface-700 rounded-full h-2.5 overflow-hidden"
              >
                <div
                  class="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full transition-all duration-500"
                  :style="{ width: vidProgress + '%' }"
                />
              </div>
            </div>

            <!-- Metrics -->
            <div v-if="vidIsProcessing" class="grid grid-cols-3 gap-3">
              <div class="bg-surface-700/40 rounded-xl p-3 text-center">
                <div class="text-lg font-bold text-brand-400">
                  {{ vidJob.current_people ?? 0 }}
                </div>
                <div
                  class="text-[10px] text-surface-500 uppercase tracking-wide"
                >
                  pessoas/frame
                </div>
              </div>
              <div class="bg-surface-700/40 rounded-xl p-3 text-center">
                <div class="text-lg font-bold text-surface-300">
                  {{ vidJob.processing_fps ?? 0 }}
                </div>
                <div
                  class="text-[10px] text-surface-500 uppercase tracking-wide"
                >
                  fps proc.
                </div>
              </div>
              <div class="bg-surface-700/40 rounded-xl p-3 text-center">
                <div class="text-lg font-bold text-surface-300">
                  {{ vidEta }}
                </div>
                <div
                  class="text-[10px] text-surface-500 uppercase tracking-wide"
                >
                  ETA
                </div>
              </div>
            </div>

            <!-- Completed result -->
            <div v-if="vidCompleted" class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="bg-surface-700/40 rounded-xl p-3 text-center">
                  <div class="text-xl font-bold text-brand-400">
                    {{ vidJob.avg_people?.toFixed(1) ?? '—' }}
                  </div>
                  <div
                    class="text-[10px] text-surface-500 uppercase tracking-wide"
                  >
                    Média pessoas
                  </div>
                </div>
                <div class="bg-surface-700/40 rounded-xl p-3 text-center">
                  <div class="text-xl font-bold text-yellow-400">
                    {{ vidJob.max_people ?? '—' }}
                  </div>
                  <div
                    class="text-[10px] text-surface-500 uppercase tracking-wide"
                  >
                    Máx. pessoas
                  </div>
                </div>
              </div>

              <div class="bg-surface-700/30 rounded-xl p-3 space-y-1.5 text-xs">
                <div class="flex justify-between text-surface-400">
                  <span>Resolução</span
                  ><span class="text-surface-300">{{ vidJob.resolution }}</span>
                </div>
                <div class="flex justify-between text-surface-400">
                  <span>FPS original</span
                  ><span class="text-surface-300">{{ vidJob.fps }} fps</span>
                </div>
                <div class="flex justify-between text-surface-400">
                  <span>Duração</span
                  ><span class="text-surface-300">{{ vidJob.duration }}s</span>
                </div>
                <div class="flex justify-between text-surface-400">
                  <span>Frames</span
                  ><span class="text-surface-300">{{
                    vidJob.total_frames
                  }}</span>
                </div>
                <div class="flex justify-between text-surface-400">
                  <span>Blur aplicado</span>
                  <span
                    :class="
                      vidJob.blur_faces ? 'text-purple-400' : 'text-surface-400'
                    "
                  >
                    {{ vidJob.blur_faces ? '✅ Sim' : '❌ Não' }}
                  </span>
                </div>
              </div>

              <a
                v-if="vidJob.output_url"
                :href="vidJob.output_url"
                download
                class="flex items-center justify-center gap-2 w-full py-2.5 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 text-green-400 font-semibold text-sm rounded-xl transition-colors"
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
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Baixar vídeo processado
              </a>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div
          v-if="vidError"
          class="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400 flex items-center gap-2"
        >
          <span>⚠️</span> {{ vidError }}
        </div>

        <!-- Process button -->
        <button
          v-if="vidFile && !vidJob"
          @click="startVideoProcessing"
          :disabled="vidLoading"
          :class="[
            'w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all',
            vidLoading
              ? 'bg-surface-700 text-surface-400 cursor-not-allowed'
              : 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20'
          ]"
        >
          <template v-if="vidLoading">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Enviando...
          </template>
          <template v-else> <span>🎬</span> Processar Vídeo </template>
        </button>

        <!-- New video button after completion -->
        <button
          v-if="vidCompleted"
          @click="clearVid"
          class="w-full flex items-center justify-center gap-2 py-2.5 bg-surface-700/60 hover:bg-surface-700 text-surface-300 font-medium text-sm rounded-xl transition-colors border border-surface-600/50"
        >
          <span>🔄</span> Processar outro vídeo
        </button>
      </div>

      <!-- Right: info panel -->
      <div class="space-y-4">
        <!-- How it works -->
        <div
          class="bg-surface-800/60 border border-surface-700/50 rounded-xl p-5 space-y-3"
        >
          <h3
            class="text-sm font-semibold text-surface-200 flex items-center gap-2"
          >
            <span>ℹ️</span> Sobre o processamento
          </h3>
          <p class="text-xs text-surface-400 leading-relaxed">
            Cada frame do vídeo é processado individualmente pela pipeline de
            detecção. O resultado é um novo vídeo com anotações visuais,
            contagem de pessoas e, opcionalmente, rostos desfocados.
          </p>
          <div class="space-y-2 pt-1">
            <div
              v-for="tip in [
                {
                  icon: '⚡',
                  text: 'Processamento assíncrono — não trava o navegador'
                },
                {
                  icon: '🎯',
                  text: 'HOG detecta corpos inteiros em cada frame'
                },
                {
                  icon: '😊',
                  text: 'Haar Cascade detecta rostos frontais e de perfil'
                },
                {
                  icon: '🙈',
                  text: 'Blur opcional preserva privacidade no vídeo final'
                },
                { icon: '📥', text: 'Baixe o vídeo processado ao final' }
              ]"
              :key="tip.text"
              class="flex items-start gap-2.5 text-xs text-surface-400"
            >
              <span class="shrink-0 mt-0.5">{{ tip.icon }}</span>
              <span>{{ tip.text }}</span>
            </div>
          </div>
        </div>

        <!-- Formats -->
        <div
          class="bg-surface-800/40 border border-surface-700/30 rounded-xl p-4"
        >
          <h3
            class="text-xs font-semibold text-surface-300 uppercase tracking-wide mb-3"
          >
            Formatos suportados
          </h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="fmt in ['MP4', 'AVI', 'MOV', 'MKV', 'WEBM']"
              :key="fmt"
              class="px-2.5 py-1 bg-surface-700/50 border border-surface-600/40 rounded-lg text-xs text-surface-300 font-mono"
            >
              {{ fmt }}
            </span>
          </div>
        </div>

        <!-- Blur warning -->
        <div
          :class="[
            'rounded-xl p-4 border',
            blurFaces
              ? 'bg-purple-600/10 border-purple-500/30'
              : 'bg-surface-800/40 border-surface-700/30'
          ]"
        >
          <div class="flex items-start gap-3">
            <span class="text-2xl shrink-0">{{ blurFaces ? '🙈' : '👁️' }}</span>
            <div>
              <p class="text-sm font-semibold text-surface-200">
                {{
                  blurFaces
                    ? 'Blur de rostos ativado'
                    : 'Blur de rostos desativado'
                }}
              </p>
              <p class="text-xs text-surface-400 mt-0.5 leading-relaxed">
                {{
                  blurFaces
                    ? 'Todos os rostos detectados serão desfocados no vídeo de saída.'
                    : 'As identidades das pessoas serão visíveis no vídeo de saída. Ative o toggle no topo para anonimizar.'
                }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
