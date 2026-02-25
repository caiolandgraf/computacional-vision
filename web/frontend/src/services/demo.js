/**
 * Demo Mode Service
 *
 * Provides mock data and simulated API responses for when the frontend
 * is running without a backend (e.g. GitHub Pages deployment).
 *
 * This allows the full UI to be showcased as a demo/portfolio piece.
 */

// ── Demo Detection ──────────────────────────────────────────

/** @type {boolean|null} cached result */
let _isDemoMode = null
let _backendChecked = false

/**
 * Returns true if the app was built for GitHub Pages demo mode.
 * Falls back to runtime backend check.
 */
export function isStaticDemoMode() {
  if (typeof __APP_MODE__ !== 'undefined' && __APP_MODE__ === 'demo') {
    return true
  }
  return false
}

/**
 * Checks whether the backend is reachable.
 * Caches the result after first successful/failed check.
 */
export async function checkBackendAvailable() {
  if (_backendChecked) return !_isDemoMode

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch('/health', {
      signal: controller.signal,
      headers: { Accept: 'application/json' }
    })
    clearTimeout(timeout)

    if (res.ok) {
      _isDemoMode = false
      _backendChecked = true
      return true
    }
  } catch {
    // Backend not reachable
  }

  _isDemoMode = true
  _backendChecked = true
  return false
}

/**
 * Returns true if the app should operate in demo mode
 * (static build or unreachable backend).
 */
export function isDemoMode() {
  if (isStaticDemoMode()) return true
  if (_isDemoMode !== null) return _isDemoMode
  // Not yet determined — assume demo if static build flag is set
  return isStaticDemoMode()
}

/**
 * Force demo mode on (useful after a failed health check at runtime).
 */
export function enableDemoMode() {
  _isDemoMode = true
  _backendChecked = true
}

/**
 * Reset demo mode detection (e.g. when user wants to retry backend).
 */
export function resetDemoMode() {
  _isDemoMode = null
  _backendChecked = false
}

// ── Mock Data ───────────────────────────────────────────────

const DEMO_TIMESTAMP = new Date().toISOString()

function randomBetween(min, max, decimals = 1) {
  const val = Math.random() * (max - min) + min
  return Number(val.toFixed(decimals))
}

function generateDemoStats(method = 'combined') {
  const coverage = randomBetween(15, 75)
  const totalPixels = 640 * 480
  const grassPixels = Math.round((coverage / 100) * totalPixels)

  return {
    coverage_percentage: coverage,
    grass_pixels: grassPixels,
    total_pixels: totalPixels,
    confidence: randomBetween(0.7, 0.99, 4),
    method
  }
}

function generateDemoDensity() {
  const classifications = ['Baixa', 'Média', 'Alta']
  const cls = classifications[Math.floor(Math.random() * 3)]

  return {
    classification: cls,
    num_regions: Math.floor(Math.random() * 20) + 1,
    average_area: randomBetween(500, 5000, 0),
    largest_area: randomBetween(5000, 30000, 0)
  }
}

function demoResultFilename(prefix = 'demo', ext = 'jpg') {
  const ts = Date.now()
  return `${prefix}_${ts}.${ext}`
}

function generateDemoResults(count = 8) {
  const results = []
  const types = [
    'image',
    'image',
    'image',
    'image',
    'video',
    'image',
    'image',
    'video'
  ]
  const methods = ['color', 'texture', 'combined', 'combined']
  const now = Date.now()

  for (let i = 0; i < count; i++) {
    const type = types[i % types.length]
    const method = methods[i % methods.length]
    const created = new Date(now - i * 3600 * 1000 * (1 + Math.random() * 5))

    results.push({
      filename: `${type === 'video' ? 'video' : 'analysis'}_${method}_${created.getTime()}.${type === 'video' ? 'mp4' : 'jpg'}`,
      type,
      size_kb:
        type === 'video'
          ? randomBetween(2000, 15000, 0)
          : randomBetween(50, 500, 0),
      created_at: created.toISOString(),
      method,
      coverage: randomBetween(10, 80),
      url: '#'
    })
  }

  return results
}

function generateDemoVideoJobs() {
  return [
    {
      id: 'demo_job_001',
      status: 'completed',
      filename: 'demo_video_1.mp4',
      method: 'combined',
      visual_mode: '1',
      quality: '1',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      completed_at: new Date(Date.now() - 6800000).toISOString(),
      current_frame: 450,
      total_frames: 450,
      progress: 100.0,
      avg_coverage: 34.5,
      max_coverage: 62.1,
      min_coverage: 8.3,
      processing_fps: 12.4,
      fps: 30,
      resolution: '1280x720',
      duration: 15.0,
      output_url: '#',
      output_file: 'demo_video_overlay.mp4'
    },
    {
      id: 'demo_job_002',
      status: 'completed',
      filename: 'demo_video_2.mp4',
      method: 'color',
      visual_mode: '2',
      quality: '1',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      completed_at: new Date(Date.now() - 3200000).toISOString(),
      current_frame: 300,
      total_frames: 300,
      progress: 100.0,
      avg_coverage: 21.2,
      max_coverage: 45.0,
      min_coverage: 5.1,
      processing_fps: 18.7,
      fps: 30,
      resolution: '640x480',
      duration: 10.0,
      output_url: '#',
      output_file: 'demo_video_2_overlay.mp4'
    }
  ]
}

// 1×1 green pixel PNG as base64 (tiny placeholder)
const PLACEHOLDER_PIXEL =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

// Generate a simple SVG as a demo "analyzed" image
function generateDemoSvgImage(
  width = 640,
  height = 480,
  label = 'Demo',
  coverage = 42.5
) {
  const coverageColor =
    coverage >= 60 ? '#ef4444' : coverage >= 30 ? '#f59e0b' : '#22c55e'
  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#22c55e"/>
      <stop offset="100%" stop-color="#16a34a"/>
    </linearGradient>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#bg)"/>
  <!-- Grid pattern -->
  <g opacity="0.05" stroke="#22c55e" stroke-width="1">
    ${Array.from({ length: Math.floor(width / 40) }, (_, i) => `<line x1="${i * 40}" y1="0" x2="${i * 40}" y2="${height}"/>`).join('')}
    ${Array.from({ length: Math.floor(height / 40) }, (_, i) => `<line x1="0" y1="${i * 40}" x2="${width}" y2="${i * 40}"/>`).join('')}
  </g>
  <!-- Simulated detection boxes -->
  <rect x="80" y="120" width="180" height="140" rx="4" fill="none" stroke="#22c55e" stroke-width="2" opacity="0.8"/>
  <rect x="80" y="120" width="180" height="3" fill="#22c55e" opacity="0.6"/>
  <rect x="350" y="200" width="150" height="100" rx="4" fill="none" stroke="#f59e0b" stroke-width="2" opacity="0.7"/>
  <rect x="200" y="320" width="220" height="90" rx="4" fill="none" stroke="#22c55e" stroke-width="2" opacity="0.6"/>
  <!-- Green overlay areas -->
  <rect x="80" y="120" width="180" height="140" fill="#22c55e" opacity="0.15"/>
  <rect x="350" y="200" width="150" height="100" fill="#f59e0b" opacity="0.1"/>
  <rect x="200" y="320" width="220" height="90" fill="#22c55e" opacity="0.12"/>
  <!-- Top bar -->
  <rect x="0" y="0" width="${width}" height="50" fill="#1e293b" opacity="0.9"/>
  <rect x="0" y="0" width="${width}" height="3" fill="url(#accent)"/>
  <text x="15" y="32" font-family="Inter, system-ui, sans-serif" font-size="16" font-weight="600" fill="white">
    🌿 ${label} — Cobertura: ${coverage.toFixed(1)}%
  </text>
  <!-- Bottom bar -->
  <rect x="0" y="${height - 40}" width="${width}" height="40" fill="#1e293b" opacity="0.85"/>
  <rect x="0" y="${height - 40}" width="${width}" height="2" fill="url(#accent)"/>
  <text x="15" y="${height - 14}" font-family="Inter, system-ui, sans-serif" font-size="13" fill="#94a3b8">
    MODO DEMO — Dados simulados
  </text>
  <text x="${width - 140}" y="${height - 14}" font-family="Inter, system-ui, sans-serif" font-size="13" fill="${coverageColor}" font-weight="600">
    ${coverage.toFixed(1)}% cobertura
  </text>
  <!-- Center label -->
  <text x="${width / 2}" y="${height / 2 - 10}" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="22" font-weight="700" fill="white" opacity="0.15">
    VISÃO COMPUTACIONAL
  </text>
  <text x="${width / 2}" y="${height / 2 + 18}" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="14" fill="#64748b" opacity="0.5">
    Demo — conecte o backend para análise real
  </text>
</svg>`

  return svgToBase64(svg)
}

function svgToBase64(svg) {
  // Encode the SVG as base64 (browser-safe)
  try {
    return btoa(unescape(encodeURIComponent(svg)))
  } catch {
    return PLACEHOLDER_PIXEL
  }
}

function demoImageAsDataUrl(label, coverage) {
  const b64 = generateDemoSvgImage(640, 480, label, coverage)
  return `data:image/svg+xml;base64,${b64}`
}

// ── Mock API Responses ──────────────────────────────────────

/** Simulates a small network delay */
function delay(ms = 300) {
  return new Promise(resolve => setTimeout(resolve, ms + Math.random() * 200))
}

export const demoApi = {
  async checkHealth() {
    await delay(100)
    return {
      status: 'ok',
      timestamp: DEMO_TIMESTAMP,
      demo: true,
      components: {
        detector: true,
        pothole_detector: true,
        visualizer: true,
        tensorflow: false
      },
      output_dir: '/demo/output'
    }
  },

  async analyzeImage(
    _file,
    { method = 'combined', visualMode = 'overlay' } = {}
  ) {
    await delay(800)
    const stats = generateDemoStats(method)
    const density = generateDemoDensity()
    const coverage = stats.coverage_percentage

    return {
      success: true,
      demo: true,
      method,
      stats: {
        coverage_percentage: coverage,
        grass_pixels: stats.grass_pixels,
        total_pixels: stats.total_pixels,
        confidence: stats.confidence
      },
      density,
      images: {
        overlay: generateDemoSvgImage(
          640,
          480,
          `Overlay — ${method}`,
          coverage
        ),
        detailed: generateDemoSvgImage(
          640,
          480,
          `Detalhado — ${visualMode}`,
          coverage
        )
      },
      files: {
        overlay: '#',
        detailed: '#'
      }
    }
  },

  async analyzePothole(_file, { method = 'combined' } = {}) {
    await delay(900)
    const numPotholes = Math.floor(Math.random() * 8) + 1
    const coverage = randomBetween(2, 25)

    const potholes = Array.from({ length: numPotholes }, (_, i) => ({
      bounding_box: [
        50 + Math.floor(Math.random() * 400),
        50 + Math.floor(Math.random() * 300),
        40 + Math.floor(Math.random() * 100),
        30 + Math.floor(Math.random() * 80)
      ],
      area: randomBetween(200, 5000, 0),
      confidence_score: randomBetween(0.5, 0.95, 2)
    }))

    return {
      success: true,
      demo: true,
      method,
      stats: {
        num_potholes: numPotholes,
        total_area: potholes.reduce((s, p) => s + p.area, 0),
        coverage,
        confidence: randomBetween(0.6, 0.95, 2),
        confidence_level:
          coverage > 15 ? 'Alta' : coverage > 8 ? 'Média' : 'Baixa'
      },
      potholes,
      flags: numPotholes > 5 ? ['high_pothole_density'] : [],
      image: generateDemoSvgImage(640, 480, `Buracos — ${method}`, coverage),
      file: '#'
    }
  },

  async compareMethods(_file, { detectionType = 'grass' } = {}) {
    await delay(1200)

    if (detectionType === 'grass') {
      const methods = ['color', 'texture', 'combined']
      const results = methods.map(m => ({
        method: m,
        coverage_percentage: randomBetween(15, 70),
        confidence: randomBetween(0.6, 0.98, 4)
      }))

      return {
        success: true,
        demo: true,
        detection_type: 'grass',
        results,
        comparison_image: generateDemoSvgImage(
          960,
          480,
          'Comparação de Métodos',
          results[2].coverage_percentage
        ),
        file: '#'
      }
    }

    // Pothole comparison
    const methods = ['contour', 'texture', 'shadow', 'combined']
    return {
      success: true,
      demo: true,
      detection_type: 'pothole',
      results: methods.map(m => ({
        method: m,
        num_potholes: Math.floor(Math.random() * 10) + 1,
        total_area: randomBetween(100, 5000, 0),
        confidence: randomBetween(0.5, 0.9, 2),
        confidence_level: 'Média'
      }))
    }
  },

  async analyzeBatch(
    files,
    { method = 'combined', detectionType = 'grass' } = {}
  ) {
    await delay(1500)
    const results = Array.from({ length: files.length }, (_, i) => {
      const file = files[i]
      const coverage = randomBetween(10, 75)
      return {
        filename: file.name || `image_${i + 1}.jpg`,
        coverage,
        confidence: randomBetween(0.6, 0.98, 4),
        density: coverage > 50 ? 'Alta' : coverage > 25 ? 'Média' : 'Baixa',
        regions: Math.floor(Math.random() * 15) + 1,
        image: generateDemoSvgImage(
          640,
          480,
          file.name || `Batch ${i + 1}`,
          coverage
        ),
        file: '#'
      }
    })

    const coverages = results.map(r => r.coverage)

    return {
      success: true,
      demo: true,
      summary: {
        total: files.length,
        processed: files.length,
        avg_coverage: Number(
          (coverages.reduce((a, b) => a + b, 0) / coverages.length).toFixed(2)
        ),
        max_coverage: Math.max(...coverages),
        min_coverage: Math.min(...coverages)
      },
      results
    }
  },

  async processVideo(_file, { method = 'combined' } = {}) {
    await delay(500)
    const jobId = `demo_${Date.now().toString(36)}`

    return {
      success: true,
      demo: true,
      job_id: jobId,
      status: 'completed'
    }
  },

  async getVideoStatus(jobId) {
    await delay(200)
    return {
      id: jobId,
      status: 'completed',
      demo: true,
      filename: 'demo_video.mp4',
      method: 'combined',
      current_frame: 300,
      total_frames: 300,
      progress: 100.0,
      avg_coverage: 28.7,
      max_coverage: 55.2,
      min_coverage: 4.1,
      processing_fps: 15.3,
      fps: 30,
      resolution: '640x480',
      duration: 10.0,
      output_url: '#',
      output_file: 'demo_output.mp4',
      completed_at: new Date().toISOString()
    }
  },

  async listVideoJobs() {
    await delay(200)
    return { jobs: generateDemoVideoJobs() }
  },

  async listResults(limit = 50) {
    await delay(200)
    return {
      results: generateDemoResults(Math.min(limit, 12)),
      demo: true
    }
  },

  async deleteResult(_filename) {
    await delay(300)
    return { success: true, demo: true }
  },

  async getSettings() {
    await delay(150)
    return {
      demo: true,
      detection: {
        default_method: 'combined',
        confidence_threshold: 0.5,
        min_area: 500,
        realtime_mode: true
      },
      visualization: {
        default_visual_mode: 'overlay',
        overlay_alpha: 0.35,
        show_contours: true,
        show_bounding_boxes: true
      },
      output: {
        save_originals: false,
        jpeg_quality: 95,
        output_dir: '/demo/output'
      }
    }
  },

  async updateSettings(settings) {
    await delay(300)
    return { success: true, demo: true, settings }
  },

  /**
   * Creates a mock WebSocket-like object for webcam demo.
   * Simulates receiving processed frames.
   */
  createWebcamSocket({ onResult, onOpen, onClose, onError } = {}) {
    let running = false
    let timer = null
    let frameCount = 0
    let method = 'combined'
    let visualMode = 'fast'
    let qualityMode = '1'

    // Simulate connection
    setTimeout(() => {
      running = true
      onOpen?.()
    }, 500)

    return {
      sendFrame(_base64Data) {
        if (!running) return

        // Simulate processing delay and send back result
        if (timer) return // throttle

        timer = setTimeout(() => {
          timer = null
          frameCount++

          const coverage = randomBetween(10, 65)
          const regions = Math.floor(Math.random() * 12) + 1
          const processingTime = randomBetween(20, 150, 1)

          onResult?.({
            type: 'result',
            image: generateDemoSvgImage(
              640,
              480,
              `${visualMode.toUpperCase()} — Demo`,
              coverage
            ),
            stats: {
              coverage: Number(coverage.toFixed(2)),
              regions,
              processing_time_ms: processingTime,
              method,
              visual_mode: visualMode,
              quality_mode: qualityMode,
              fps: randomBetween(8, 25, 1)
            }
          })
        }, 80)
      },

      sendConfig(config) {
        if (config.method !== undefined) method = config.method
        if (config.visualMode !== undefined) visualMode = config.visualMode
        if (config.qualityMode !== undefined) qualityMode = config.qualityMode
      },

      get readyState() {
        return running ? 1 : 3 // WebSocket.OPEN : WebSocket.CLOSED
      },

      get isConnected() {
        return running
      },

      close() {
        running = false
        if (timer) {
          clearTimeout(timer)
          timer = null
        }
        onClose?.({ code: 1000 })
      }
    }
  }
}

/**
 * Helper to get a demo image data URL for display.
 */
export function getDemoImageUrl(label = 'Demo', coverage = 35) {
  return demoImageAsDataUrl(label, coverage)
}

export default demoApi
