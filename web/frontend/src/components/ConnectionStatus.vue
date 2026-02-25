<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { checkHealth } from '@/services/api'
import { isDemoMode, isStaticDemoMode } from '@/services/demo'

const props = defineProps({
  /** Polling interval in milliseconds */
  interval: {
    type: Number,
    default: 30000
  },
  /** Show detailed info (components, versions) */
  detailed: {
    type: Boolean,
    default: false
  },
  /** Compact inline badge mode */
  compact: {
    type: Boolean,
    default: false
  },
  /** Auto-hide when connected (only show errors) */
  autoHide: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['status-change', 'health-data'])

const status = ref('checking') // 'checking' | 'connected' | 'disconnected' | 'error' | 'demo'
const healthData = ref(null)
const lastChecked = ref(null)
const errorMessage = ref('')
const retryCount = ref(0)
const showDetails = ref(false)
let pollTimer = null
let retryTimer = null

const MAX_RETRY_DELAY = 30000
const BASE_RETRY_DELAY = 2000

const statusConfig = computed(() => {
  switch (status.value) {
    case 'demo':
      return {
        label: 'Demo',
        icon: '🟣',
        dotClass: 'bg-purple-500',
        badgeBg: 'bg-purple-500/10 border-purple-500/25',
        badgeText: 'text-purple-400',
        pulseClass: 'animate-pulse-slow'
      }
    case 'connected':
      return {
        label: 'Online',
        icon: '🟢',
        dotClass: 'bg-brand-500',
        badgeBg: 'bg-brand-500/10 border-brand-500/25',
        badgeText: 'text-brand-400',
        pulseClass: 'animate-pulse-slow'
      }
    case 'disconnected':
      return {
        label: 'Offline',
        icon: '🔴',
        dotClass: 'bg-red-500',
        badgeBg: 'bg-red-500/10 border-red-500/25',
        badgeText: 'text-red-400',
        pulseClass: ''
      }
    case 'error':
      return {
        label: 'Erro',
        icon: '🟡',
        dotClass: 'bg-yellow-500',
        badgeBg: 'bg-yellow-500/10 border-yellow-500/25',
        badgeText: 'text-yellow-400',
        pulseClass: ''
      }
    default:
      return {
        label: 'Verificando...',
        icon: '⚪',
        dotClass: 'bg-surface-500',
        badgeBg: 'bg-surface-700/50 border-surface-600/50',
        badgeText: 'text-surface-400',
        pulseClass: 'animate-pulse'
      }
  }
})

const componentsList = computed(() => {
  if (!healthData.value?.components) return []
  return Object.entries(healthData.value.components).map(
    ([name, available]) => ({
      name: formatComponentName(name),
      available
    })
  )
})

const lastCheckedFormatted = computed(() => {
  if (!lastChecked.value) return 'Nunca'
  const now = new Date()
  const diff = Math.floor((now - lastChecked.value) / 1000)
  if (diff < 5) return 'Agora'
  if (diff < 60) return `${diff}s atrás`
  if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`
  return lastChecked.value.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
})

const isVisible = computed(() => {
  // Always show the badge in demo mode so users know it's a demo
  if (status.value === 'demo') return true
  if (!props.autoHide) return true
  return status.value !== 'connected'
})

function formatComponentName(name) {
  const labels = {
    detector: 'Detector de Mato',
    pothole_detector: 'Detector de Buracos',
    visualizer: 'Visualizador',
    tensorflow: 'TensorFlow (Deep Learning)'
  }
  return (
    labels[name] ||
    name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  )
}

async function checkConnection() {
  // If running as a static GitHub Pages demo, skip real health checks
  if (isStaticDemoMode()) {
    status.value = 'demo'
    healthData.value = {
      status: 'ok',
      demo: true,
      timestamp: new Date().toISOString(),
      components: {
        detector: true,
        pothole_detector: true,
        visualizer: true,
        tensorflow: false
      },
      output_dir: '/demo/output'
    }
    lastChecked.value = new Date()
    errorMessage.value = ''
    retryCount.value = 0
    emit('status-change', 'demo')
    emit('health-data', healthData.value)
    // No need to keep polling in demo mode
    return
  }

  try {
    const data = await checkHealth()
    healthData.value = data
    lastChecked.value = new Date()
    errorMessage.value = ''
    retryCount.value = 0

    // If the health response came from demo fallback, mark as demo
    const newStatus = data.demo
      ? 'demo'
      : data.status === 'ok'
        ? 'connected'
        : 'error'
    if (status.value !== newStatus) {
      status.value = newStatus
      emit('status-change', newStatus)
    }
    emit('health-data', data)

    // In demo mode, don't keep polling (backend is unreachable)
    if (newStatus === 'demo') return

    // Reset to normal polling interval
    startPolling()
  } catch (err) {
    // If demo mode was activated (e.g. by api.js fallback), show demo status
    if (isDemoMode()) {
      status.value = 'demo'
      lastChecked.value = new Date()
      errorMessage.value = ''
      emit('status-change', 'demo')
      return
    }

    lastChecked.value = new Date()
    errorMessage.value = err.message || 'Servidor não respondeu'

    const newStatus = 'disconnected'
    if (status.value !== newStatus) {
      status.value = newStatus
      emit('status-change', newStatus)
    }

    // Exponential backoff for retries
    retryCount.value++
    const delay = Math.min(
      BASE_RETRY_DELAY * Math.pow(1.5, retryCount.value - 1),
      MAX_RETRY_DELAY
    )
    scheduleRetry(delay)
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(checkConnection, props.interval)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }
}

function scheduleRetry(delay) {
  stopPolling()
  retryTimer = setTimeout(() => {
    checkConnection()
  }, delay)
}

function manualRetry() {
  status.value = 'checking'
  retryCount.value = 0
  checkConnection()
}

function toggleDetails() {
  showDetails.value = !showDetails.value
}

onMounted(() => {
  checkConnection()
})

onUnmounted(() => {
  stopPolling()
})

defineExpose({
  status,
  healthData,
  checkConnection,
  manualRetry
})
</script>

<template>
  <!-- Compact badge mode -->
  <div v-if="compact && isVisible">
    <button
      @click="toggleDetails"
      :class="[
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all duration-200',
        'hover:brightness-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50',
        statusConfig.badgeBg,
        statusConfig.badgeText
      ]"
      :title="`Backend: ${statusConfig.label}`"
    >
      <div
        :class="[
          'w-1.5 h-1.5 rounded-full shrink-0',
          statusConfig.dotClass,
          statusConfig.pulseClass
        ]"
      />
      <span>{{ statusConfig.label }}</span>
    </button>

    <!-- Compact dropdown details -->
    <Transition name="dropdown">
      <div
        v-if="showDetails"
        class="absolute top-full right-0 mt-1.5 w-72 z-50 rounded-xl border border-surface-700/50 bg-surface-800/95 backdrop-blur-xl shadow-2xl shadow-black/30 overflow-hidden"
      >
        <div class="p-3 space-y-2.5">
          <!-- Status header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div
                :class="[
                  'w-2 h-2 rounded-full',
                  statusConfig.dotClass,
                  statusConfig.pulseClass
                ]"
              />
              <span :class="['text-sm font-semibold', statusConfig.badgeText]">
                {{ statusConfig.label }}
              </span>
            </div>
            <span class="text-[10px] text-surface-500">{{
              lastCheckedFormatted
            }}</span>
          </div>

          <!-- Demo mode info -->
          <div
            v-if="status === 'demo'"
            class="flex items-start gap-2 p-2 rounded-lg bg-purple-500/8 border border-purple-500/15"
          >
            <span class="text-xs shrink-0 mt-px">🎭</span>
            <div>
              <p class="text-xs text-purple-400 font-medium">
                Modo Demonstração
              </p>
              <p class="text-[10px] text-surface-500 mt-0.5">
                Interface rodando sem backend. Dados são simulados para
                visualização.
              </p>
            </div>
          </div>

          <!-- Error message -->
          <div
            v-if="errorMessage && status !== 'demo'"
            class="flex items-start gap-2 p-2 rounded-lg bg-red-500/8 border border-red-500/15"
          >
            <span class="text-xs shrink-0 mt-px">⚠️</span>
            <div>
              <p class="text-xs text-red-400 font-medium">{{ errorMessage }}</p>
              <p
                v-if="retryCount > 0"
                class="text-[10px] text-surface-500 mt-0.5"
              >
                Tentativa {{ retryCount }} de reconexão...
              </p>
            </div>
          </div>

          <!-- Components -->
          <div v-if="componentsList.length > 0" class="space-y-1">
            <p
              class="text-[10px] font-semibold text-surface-500 uppercase tracking-wider"
            >
              Componentes
            </p>
            <div
              v-for="comp in componentsList"
              :key="comp.name"
              class="flex items-center justify-between py-1"
            >
              <span class="text-xs text-surface-300">{{ comp.name }}</span>
              <span
                :class="[
                  'text-[10px] font-semibold px-1.5 py-0.5 rounded-md',
                  comp.available
                    ? 'bg-brand-500/15 text-brand-400'
                    : 'bg-surface-700 text-surface-500'
                ]"
              >
                {{ comp.available ? '✓ OK' : '✗ N/A' }}
              </span>
            </div>
          </div>

          <!-- Retry button -->
          <button
            v-if="status !== 'connected' && status !== 'demo'"
            @click="manualRetry"
            class="w-full btn-secondary btn-sm text-xs"
          >
            🔄 Tentar reconectar
          </button>
        </div>
      </div>
    </Transition>
  </div>

  <!-- Full banner mode (for disconnected state) -->
  <Transition name="slide-banner">
    <div
      v-if="!compact && isVisible"
      :class="[
        'rounded-xl border overflow-hidden transition-all duration-300',
        statusConfig.badgeBg
      ]"
    >
      <div class="flex items-center gap-3 px-4 py-3">
        <!-- Status dot -->
        <div
          :class="[
            'w-2.5 h-2.5 rounded-full shrink-0',
            statusConfig.dotClass,
            statusConfig.pulseClass
          ]"
        />

        <!-- Status info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span :class="['text-sm font-semibold', statusConfig.badgeText]">
              Backend {{ statusConfig.label }}
            </span>
            <span v-if="retryCount > 0" class="text-[10px] text-surface-500">
              (tentativa {{ retryCount }})
            </span>
          </div>
          <p
            v-if="status === 'demo'"
            class="text-xs text-purple-400/70 mt-0.5 truncate"
          >
            Modo demonstração — dados simulados
          </p>
          <p
            v-else-if="errorMessage"
            class="text-xs text-surface-400 mt-0.5 truncate"
          >
            {{ errorMessage }}
          </p>
          <p
            v-else-if="status === 'checking'"
            class="text-xs text-surface-400 mt-0.5"
          >
            Verificando conexão com o servidor...
          </p>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 shrink-0">
          <!-- Last checked -->
          <span
            v-if="lastChecked"
            class="text-[10px] text-surface-500 hidden sm:inline"
          >
            {{ lastCheckedFormatted }}
          </span>

          <!-- Retry button -->
          <button
            v-if="status === 'disconnected' || status === 'error'"
            @click="manualRetry"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors bg-surface-700/50 text-surface-300 hover:bg-surface-700 hover:text-white"
          >
            🔄 Reconectar
          </button>

          <!-- Details toggle -->
          <button
            v-if="detailed && healthData"
            @click="toggleDetails"
            class="p-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/50 transition-colors"
            :title="showDetails ? 'Ocultar detalhes' : 'Mostrar detalhes'"
          >
            <svg
              :class="[
                'w-4 h-4 transition-transform duration-200',
                showDetails && 'rotate-180'
              ]"
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
          </button>
        </div>
      </div>

      <!-- Expandable details panel -->
      <Transition name="expand">
        <div
          v-if="showDetails && healthData"
          class="border-t border-surface-700/30 px-4 py-3 space-y-3"
        >
          <!-- Components grid -->
          <div v-if="componentsList.length > 0">
            <p
              class="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2"
            >
              Componentes do Sistema
            </p>
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="comp in componentsList"
                :key="comp.name"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg border',
                  comp.available
                    ? 'bg-brand-500/5 border-brand-500/15'
                    : 'bg-surface-800/40 border-surface-700/30'
                ]"
              >
                <div
                  :class="[
                    'w-1.5 h-1.5 rounded-full',
                    comp.available ? 'bg-brand-500' : 'bg-surface-600'
                  ]"
                />
                <span
                  :class="[
                    'text-xs',
                    comp.available ? 'text-surface-200' : 'text-surface-500'
                  ]"
                >
                  {{ comp.name }}
                </span>
              </div>
            </div>
          </div>

          <!-- Server info -->
          <div
            v-if="healthData.output_dir"
            class="flex items-center gap-2 text-[10px] text-surface-500"
          >
            <span>📂</span>
            <span class="font-mono truncate">{{ healthData.output_dir }}</span>
          </div>

          <!-- Timestamp -->
          <div
            v-if="healthData.timestamp"
            class="flex items-center gap-2 text-[10px] text-surface-500"
          >
            <span>🕐</span>
            <span
              >Servidor:
              {{ new Date(healthData.timestamp).toLocaleString('pt-BR') }}</span
            >
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
.dropdown-enter-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-leave-active {
  transition: all 0.15s ease-in;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}

.slide-banner-enter-active {
  transition: all 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
}
.slide-banner-leave-active {
  transition: all 0.25s ease-in;
}
.slide-banner-enter-from {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}
.slide-banner-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}

.expand-enter-active {
  transition: all 0.3s ease-out;
  overflow: hidden;
}
.expand-leave-active {
  transition: all 0.2s ease-in;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
