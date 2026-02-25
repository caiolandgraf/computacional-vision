import axios from 'axios'
import { demoApi, enableDemoMode, isDemoMode } from './demo'

const api = axios.create({
  baseURL: '',
  timeout: 300000, // 5 min para uploads grandes
  headers: {
    Accept: 'application/json'
  }
})

// ── Interceptors ────────────────────────────────────────────

api.interceptors.response.use(
  response => response,
  error => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Erro desconhecido'

    console.error(
      `[API] ${error.config?.method?.toUpperCase()} ${error.config?.url} → ${message}`
    )
    return Promise.reject({
      message,
      status: error.response?.status,
      raw: error
    })
  }
)

// ── Helpers ─────────────────────────────────────────────────

function buildFormData(fields) {
  const fd = new FormData()
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined && value !== null) {
      fd.append(key, value)
    }
  }
  return fd
}

function buildMultiFileFormData(files, fields = {}) {
  const fd = new FormData()
  for (const file of files) {
    fd.append('files', file)
  }
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined && value !== null) {
      fd.append(key, value)
    }
  }
  return fd
}

// ── Health ──────────────────────────────────────────────────

export async function checkHealth() {
  if (isDemoMode()) return demoApi.checkHealth()
  try {
    const { data } = await api.get('/health')
    return data
  } catch (err) {
    enableDemoMode()
    console.warn('[API] Backend unreachable — switching to demo mode')
    return demoApi.checkHealth()
  }
}

// ── Análise de Imagem (Mato) ────────────────────────────────

export async function analyzeImage(
  file,
  { method = 'combined', visualMode = 'overlay' } = {}
) {
  if (isDemoMode()) return demoApi.analyzeImage(file, { method, visualMode })
  const fd = buildFormData({
    file,
    method,
    visual_mode: visualMode
  })
  const { data } = await api.post('/api/analyze/image', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

// ── Análise de Buracos ──────────────────────────────────────

export async function analyzePothole(file, { method = 'combined' } = {}) {
  if (isDemoMode()) return demoApi.analyzePothole(file, { method })
  const fd = buildFormData({ file, method })
  const { data } = await api.post('/api/analyze/pothole', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

// ── Comparação de Métodos ───────────────────────────────────

export async function compareMethods(file, { detectionType = 'grass' } = {}) {
  if (isDemoMode()) return demoApi.compareMethods(file, { detectionType })
  const fd = buildFormData({ file, detection_type: detectionType })
  const { data } = await api.post('/api/analyze/compare', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

// ── Análise em Lote ─────────────────────────────────────────

export async function analyzeBatch(
  files,
  { method = 'combined', detectionType = 'grass' } = {}
) {
  if (isDemoMode())
    return demoApi.analyzeBatch(files, { method, detectionType })
  const fd = buildMultiFileFormData(files, {
    method,
    detection_type: detectionType
  })
  const { data } = await api.post('/api/analyze/batch', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000 // 10 min para lotes grandes
  })
  return data
}

// ── Processamento de Vídeo ──────────────────────────────────

export async function processVideo(
  file,
  { method = 'combined', visualMode = '1', quality = '1' } = {}
) {
  if (isDemoMode())
    return demoApi.processVideo(file, { method, visualMode, quality })
  const fd = buildFormData({
    file,
    method,
    visual_mode: visualMode,
    quality
  })
  const { data } = await api.post('/api/video/process', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000
  })
  return data
}

export async function getVideoStatus(jobId) {
  if (isDemoMode()) return demoApi.getVideoStatus(jobId)
  const { data } = await api.get(`/api/video/status/${jobId}`)
  return data
}

export async function listVideoJobs() {
  if (isDemoMode()) return demoApi.listVideoJobs()
  const { data } = await api.get('/api/video/jobs')
  return data
}

// Polling helper: chama callback a cada intervalo até o job completar/falhar
export function pollVideoJob(
  jobId,
  { interval = 1000, onProgress, onComplete, onError }
) {
  let timer = null
  let stopped = false

  const tick = async () => {
    if (stopped) return

    try {
      const status = await getVideoStatus(jobId)

      if (status.status === 'completed') {
        stopped = true
        onComplete?.(status)
        return
      }

      if (status.status === 'error') {
        stopped = true
        onError?.(status.error || 'Erro desconhecido no processamento')
        return
      }

      onProgress?.(status)

      if (!stopped) {
        timer = setTimeout(tick, interval)
      }
    } catch (err) {
      stopped = true
      onError?.(err.message || 'Erro ao buscar status')
    }
  }

  // Inicia
  timer = setTimeout(tick, 500)

  // Retorna função de cancelamento
  return () => {
    stopped = true
    if (timer) clearTimeout(timer)
  }
}

// ── Resultados / Galeria ────────────────────────────────────

export async function listResults(limit = 50) {
  if (isDemoMode()) return demoApi.listResults(limit)
  const { data } = await api.get('/api/results', { params: { limit } })
  return data
}

export async function deleteResult(filename) {
  if (isDemoMode()) return demoApi.deleteResult(filename)
  const { data } = await api.delete(
    `/api/results/${encodeURIComponent(filename)}`
  )
  return data
}

export function getDownloadUrl(filename) {
  return `/api/download/${encodeURIComponent(filename)}`
}

export function getFileUrl(filename) {
  return `/files/output/${encodeURIComponent(filename)}`
}

// ── Configurações ───────────────────────────────────────────

export async function getSettings() {
  if (isDemoMode()) return demoApi.getSettings()
  const { data } = await api.get('/api/settings')
  return data
}

export async function updateSettings(settings) {
  if (isDemoMode()) return demoApi.updateSettings(settings)
  const { data } = await api.put('/api/settings', settings)
  return data
}

// ── WebSocket Webcam ────────────────────────────────────────

export function createWebcamSocket({
  onResult,
  onOpen,
  onClose,
  onError
} = {}) {
  // In demo mode, return a mock socket that simulates processing
  if (isDemoMode()) {
    return demoApi.createWebcamSocket({ onResult, onOpen, onClose, onError })
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${protocol}//${host}/api/ws/webcam`

  let ws = null
  let reconnectTimer = null
  let shouldReconnect = true

  function connect() {
    ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('[WS] Webcam conectada')
      onOpen?.()
    }

    ws.onmessage = event => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'result') {
          onResult?.(msg)
        }
      } catch (err) {
        console.error('[WS] Erro ao parsear mensagem:', err)
      }
    }

    ws.onclose = event => {
      console.log('[WS] Webcam desconectada', event.code)
      onClose?.(event)
      if (shouldReconnect && event.code !== 1000) {
        reconnectTimer = setTimeout(connect, 2000)
      }
    }

    ws.onerror = err => {
      console.error('[WS] Erro:', err)
      onError?.(err)
    }
  }

  connect()

  return {
    sendFrame(base64Data) {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'frame', data: base64Data }))
      }
    },

    sendConfig({ method, visualMode, qualityMode }) {
      if (ws?.readyState === WebSocket.OPEN) {
        const payload = { type: 'config' }
        if (method !== undefined) payload.method = method
        if (visualMode !== undefined) payload.visual_mode = visualMode
        if (qualityMode !== undefined) payload.quality_mode = qualityMode
        ws.send(JSON.stringify(payload))
      }
    },

    get readyState() {
      return ws?.readyState ?? WebSocket.CLOSED
    },

    get isConnected() {
      return ws?.readyState === WebSocket.OPEN
    },

    close() {
      shouldReconnect = false
      if (reconnectTimer) clearTimeout(reconnectTimer)
      ws?.close(1000, 'Client closed')
    }
  }
}

// ── Constantes de métodos ───────────────────────────────────

export const GRASS_METHODS = [
  {
    value: 'color',
    label: 'Baseado em Cores',
    description: 'Rápido, identifica tons de verde/marrom',
    icon: '🎨'
  },
  {
    value: 'texture',
    label: 'Baseado em Textura',
    description: 'Mais preciso, analisa padrões da imagem',
    icon: '🧩'
  },
  {
    value: 'combined',
    label: 'Combinado',
    description: 'Recomendado, une cor + textura',
    icon: '⚡'
  },
  {
    value: 'deeplearning',
    label: 'Deep Learning',
    description: 'Experimental, usa redes neurais',
    icon: '🧠'
  }
]

export const POTHOLE_METHODS = [
  {
    value: 'contour',
    label: 'Análise de Contornos',
    description: 'Recomendado para a maioria dos casos',
    icon: '📐'
  },
  {
    value: 'texture',
    label: 'Análise de Textura',
    description: 'Detecta variações de textura no asfalto',
    icon: '🧩'
  },
  {
    value: 'shadow',
    label: 'Análise de Sombras',
    description: 'Detecta padrões de sombra em buracos',
    icon: '🌑'
  },
  {
    value: 'combined',
    label: 'Método Combinado',
    description: 'Melhor precisão, mais lento',
    icon: '⚡'
  }
]

export const VISUAL_MODES = [
  {
    value: 'overlay',
    label: 'Overlay Clássico',
    description: 'Sobreposição verde nas áreas detectadas'
  },
  {
    value: 'bounding_box',
    label: 'Dashboard Moderno',
    description: 'Bounding boxes com cards de informação'
  },
  {
    value: 'contour',
    label: 'Contornos',
    description: 'Apenas contornos das áreas detectadas'
  }
]

export const WEBCAM_VISUAL_MODES = [
  {
    value: 'fast',
    label: 'Rápido',
    description: 'Overlay leve, máximo FPS',
    icon: '⚡'
  },
  {
    value: 'overlay',
    label: 'Overlay Clássico',
    description: 'Sobreposição detalhada com painel',
    icon: '🎨'
  },
  {
    value: 'bounding_box',
    label: 'Bounding Boxes',
    description: 'Caixas ao redor das detecções',
    icon: '🔲'
  },
  {
    value: 'contour',
    label: 'Contornos',
    description: 'Apenas contornos numerados',
    icon: '✏️'
  }
]

export const WEBCAM_QUALITY_MODES = [
  {
    value: '1',
    label: 'Tempo Real',
    description: 'Rápido, precisão média',
    icon: '🚀'
  },
  {
    value: '2',
    label: 'Alta Precisão',
    description: 'Lento, melhor qualidade',
    icon: '🎯'
  }
]

export const VIDEO_VISUAL_MODES = [
  {
    value: '1',
    label: 'Overlay Leve',
    description: 'Estilo webcam tempo real, leve e rápido'
  },
  {
    value: '2',
    label: 'Overlay Completo',
    description: 'Estilo clássico com informações detalhadas'
  },
  {
    value: '3',
    label: 'Dashboard Moderno',
    description: 'Bounding boxes + painel lateral de dados'
  }
]

export const VIDEO_QUALITY_MODES = [
  {
    value: '1',
    label: 'Rápido',
    description: 'Modo tempo real, menor qualidade de detecção'
  },
  {
    value: '2',
    label: 'Alta Precisão',
    description: 'Processamento lento, melhor qualidade'
  }
]

export default api
