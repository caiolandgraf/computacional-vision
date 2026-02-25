<script>
import { ref, reactive } from 'vue'

// ── Composable (singleton state) ─────────────────────────────
const toasts = reactive([])
let idCounter = 0

const ICONS = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
}

const COLORS = {
  success: {
    bg: 'bg-brand-500/10',
    border: 'border-brand-500/25',
    text: 'text-brand-400',
    progress: 'bg-brand-500',
  },
  error: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/25',
    text: 'text-red-400',
    progress: 'bg-red-500',
  },
  warning: {
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/25',
    text: 'text-yellow-400',
    progress: 'bg-yellow-500',
  },
  info: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/25',
    text: 'text-blue-400',
    progress: 'bg-blue-500',
  },
}

function addToast({ type = 'info', title = '', message = '', duration = 4000, dismissible = true } = {}) {
  const id = ++idCounter

  const toast = reactive({
    id,
    type,
    title,
    message,
    duration,
    dismissible,
    visible: false,
    removing: false,
    progressWidth: 100,
    timer: null,
    progressTimer: null,
    paused: false,
  })

  toasts.push(toast)

  // Trigger enter animation on next tick
  requestAnimationFrame(() => {
    toast.visible = true
  })

  if (duration > 0) {
    startAutoClose(toast)
  }

  return id
}

function startAutoClose(toast) {
  const stepMs = 50
  const totalSteps = toast.duration / stepMs
  const decrement = 100 / totalSteps
  let elapsed = 0

  toast.progressTimer = setInterval(() => {
    if (toast.paused) return
    elapsed += stepMs
    toast.progressWidth = Math.max(0, 100 - (elapsed / toast.duration) * 100)

    if (elapsed >= toast.duration) {
      clearInterval(toast.progressTimer)
      removeToast(toast.id)
    }
  }, stepMs)
}

function pauseToast(id) {
  const toast = toasts.find((t) => t.id === id)
  if (toast) {
    toast.paused = true
  }
}

function resumeToast(id) {
  const toast = toasts.find((t) => t.id === id)
  if (toast) {
    toast.paused = false
  }
}

function removeToast(id) {
  const index = toasts.findIndex((t) => t.id === id)
  if (index === -1) return

  const toast = toasts[index]
  if (toast.removing) return
  toast.removing = true
  toast.visible = false

  if (toast.progressTimer) {
    clearInterval(toast.progressTimer)
  }

  // Wait for leave animation to complete before removing from array
  setTimeout(() => {
    const idx = toasts.findIndex((t) => t.id === id)
    if (idx !== -1) {
      toasts.splice(idx, 1)
    }
  }, 350)
}

function clearAllToasts() {
  const ids = toasts.map((t) => t.id)
  ids.forEach(removeToast)
}

export function useToast() {
  return {
    toasts,
    addToast,
    removeToast,
    clearAllToasts,
    success(titleOrMessage, message) {
      if (message) return addToast({ type: 'success', title: titleOrMessage, message })
      return addToast({ type: 'success', title: titleOrMessage })
    },
    error(titleOrMessage, message) {
      if (message) return addToast({ type: 'error', title: titleOrMessage, message, duration: 6000 })
      return addToast({ type: 'error', title: titleOrMessage, duration: 6000 })
    },
    warning(titleOrMessage, message) {
      if (message) return addToast({ type: 'warning', title: titleOrMessage, message, duration: 5000 })
      return addToast({ type: 'warning', title: titleOrMessage, duration: 5000 })
    },
    info(titleOrMessage, message) {
      if (message) return addToast({ type: 'info', title: titleOrMessage, message })
      return addToast({ type: 'info', title: titleOrMessage })
    },
  }
}
</script>

<script setup>
const { toasts: toastList, removeToast: dismiss } = useToast()

function getColors(type) {
  return COLORS[type] || COLORS.info
}

function getIcon(type) {
  return ICONS[type] || ICONS.info
}

function onMouseEnter(toast) {
  pauseToast(toast.id)
}

function onMouseLeave(toast) {
  resumeToast(toast.id)
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed top-4 right-4 z-[99999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full sm:max-w-md"
      aria-live="polite"
      aria-atomic="true"
    >
      <TransitionGroup
        name="toast"
        tag="div"
        class="flex flex-col gap-2.5"
      >
        <div
          v-for="toast in toastList"
          :key="toast.id"
          :class="[
            'pointer-events-auto relative overflow-hidden rounded-xl border backdrop-blur-md shadow-2xl shadow-black/20',
            'transition-all duration-300 ease-out',
            getColors(toast.type).bg,
            getColors(toast.type).border,
            toast.visible && !toast.removing
              ? 'opacity-100 translate-x-0 scale-100'
              : 'opacity-0 translate-x-8 scale-95',
          ]"
          @mouseenter="onMouseEnter(toast)"
          @mouseleave="onMouseLeave(toast)"
          role="alert"
        >
          <div class="flex items-start gap-3 p-3.5 pr-10">
            <!-- Icon -->
            <span class="text-lg shrink-0 mt-0.5 select-none">
              {{ getIcon(toast.type) }}
            </span>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <p
                v-if="toast.title"
                :class="['text-sm font-semibold leading-tight', getColors(toast.type).text]"
              >
                {{ toast.title }}
              </p>
              <p
                v-if="toast.message"
                :class="[
                  'text-xs leading-relaxed text-surface-300',
                  toast.title ? 'mt-0.5' : '',
                ]"
              >
                {{ toast.message }}
              </p>
            </div>

            <!-- Dismiss button -->
            <button
              v-if="toast.dismissible"
              @click="dismiss(toast.id)"
              class="absolute top-2.5 right-2.5 p-1 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/50 transition-colors"
              aria-label="Fechar notificação"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Progress bar -->
          <div
            v-if="toast.duration > 0"
            class="h-[2px] w-full bg-surface-700/30"
          >
            <div
              :class="['h-full transition-all duration-100 ease-linear rounded-full', getColors(toast.type).progress]"
              :style="{ width: toast.progressWidth + '%', opacity: toast.paused ? 0.4 : 0.6 }"
            />
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
}

.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.06, 0.71, 0.55, 1);
  position: absolute;
  width: 100%;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px) scale(0.92);
}

.toast-move {
  transition: transform 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
}
</style>
