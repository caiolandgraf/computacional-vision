<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Confirmar ação',
  },
  message: {
    type: String,
    default: 'Tem certeza que deseja continuar?',
  },
  icon: {
    type: String,
    default: '⚠️',
  },
  confirmLabel: {
    type: String,
    default: 'Confirmar',
  },
  cancelLabel: {
    type: String,
    default: 'Cancelar',
  },
  variant: {
    type: String,
    default: 'danger',
    validator: (v) => ['danger', 'warning', 'info', 'primary'].includes(v),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  persistent: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const dialogRef = ref(null)
const visible = ref(false)
const animating = ref(false)

const variantStyles = {
  danger: {
    iconBg: 'bg-red-500/15 border-red-500/20',
    iconText: 'text-red-400',
    confirmBtn: 'bg-red-600/90 text-white shadow-lg shadow-red-600/20 hover:bg-red-500 hover:shadow-red-500/30 focus-visible:ring-red-500',
    ring: 'ring-red-500/10',
  },
  warning: {
    iconBg: 'bg-yellow-500/15 border-yellow-500/20',
    iconText: 'text-yellow-400',
    confirmBtn: 'bg-yellow-600/90 text-white shadow-lg shadow-yellow-600/20 hover:bg-yellow-500 hover:shadow-yellow-500/30 focus-visible:ring-yellow-500',
    ring: 'ring-yellow-500/10',
  },
  info: {
    iconBg: 'bg-blue-500/15 border-blue-500/20',
    iconText: 'text-blue-400',
    confirmBtn: 'bg-blue-600/90 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-500 hover:shadow-blue-500/30 focus-visible:ring-blue-500',
    ring: 'ring-blue-500/10',
  },
  primary: {
    iconBg: 'bg-brand-500/15 border-brand-500/20',
    iconText: 'text-brand-400',
    confirmBtn: 'bg-brand-600 text-white shadow-lg shadow-brand-600/20 hover:bg-brand-500 hover:shadow-brand-500/30 focus-visible:ring-brand-500',
    ring: 'ring-brand-500/10',
  },
}

function getStyles() {
  return variantStyles[props.variant] || variantStyles.danger
}

function open() {
  visible.value = true
  animating.value = true
  requestAnimationFrame(() => {
    animating.value = false
  })
}

function close() {
  if (props.loading) return
  animating.value = true
  visible.value = false
  setTimeout(() => {
    animating.value = false
    emit('update:modelValue', false)
  }, 250)
}

function onConfirm() {
  emit('confirm')
}

function onCancel() {
  emit('cancel')
  close()
}

function onOverlayClick() {
  if (!props.persistent && !props.loading) {
    onCancel()
  }
}

function onKeydown(e) {
  if (!props.modelValue) return

  if (e.key === 'Escape' && !props.persistent && !props.loading) {
    e.preventDefault()
    onCancel()
  }

  if (e.key === 'Enter' && !props.loading) {
    e.preventDefault()
    onConfirm()
  }

  // Trap focus inside dialog
  if (e.key === 'Tab' && dialogRef.value) {
    const focusable = dialogRef.value.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )
    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      open()
      // Auto-focus the cancel button (safer default)
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const cancelBtn = dialogRef.value?.querySelector('[data-cancel-btn]')
          cancelBtn?.focus()
        })
      })
    } else if (visible.value) {
      close()
    }
  },
  { immediate: true }
)

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <!-- Backdrop overlay -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
          :class="visible && !animating ? 'opacity-100' : 'opacity-0'"
          @click="onOverlayClick"
        />

        <!-- Dialog panel -->
        <div
          ref="dialogRef"
          :class="[
            'relative w-full max-w-md rounded-2xl border border-surface-700/60 bg-surface-800/95 backdrop-blur-xl shadow-2xl shadow-black/30',
            'transition-all duration-300 ease-out',
            visible && !animating
              ? 'opacity-100 scale-100 translate-y-0'
              : 'opacity-0 scale-95 translate-y-4',
          ]"
        >
          <!-- Close button (top right) -->
          <button
            v-if="!persistent && !loading"
            @click="onCancel"
            class="absolute top-3 right-3 p-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/60 transition-colors z-10"
            aria-label="Fechar"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Content -->
          <div class="p-6 sm:p-7">
            <!-- Icon -->
            <div class="flex justify-center mb-4">
              <div
                :class="[
                  'w-14 h-14 flex items-center justify-center rounded-2xl border text-2xl',
                  getStyles().iconBg,
                ]"
              >
                {{ icon }}
              </div>
            </div>

            <!-- Title -->
            <h3 class="text-center text-lg font-bold text-white tracking-tight">
              {{ title }}
            </h3>

            <!-- Message -->
            <p class="mt-2 text-center text-sm text-surface-400 leading-relaxed max-w-xs mx-auto">
              {{ message }}
            </p>

            <!-- Slot for extra content (e.g. input fields, details) -->
            <div v-if="$slots.default" class="mt-4">
              <slot />
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 px-6 sm:px-7 pb-6 sm:pb-7">
            <button
              data-cancel-btn
              @click="onCancel"
              :disabled="loading"
              :class="[
                'flex-1 inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm',
                'transition-all duration-200 ease-out',
                'bg-surface-700 text-surface-100 border border-surface-600',
                'hover:bg-surface-600 hover:text-white hover:border-surface-500',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-surface-500 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-800',
                'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none',
                'active:scale-[0.97]',
              ]"
            >
              {{ cancelLabel }}
            </button>

            <button
              @click="onConfirm"
              :disabled="loading"
              :class="[
                'flex-1 inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm',
                'transition-all duration-200 ease-out',
                getStyles().confirmBtn,
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-800',
                'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none',
                'active:scale-[0.97]',
              ]"
            >
              <template v-if="loading">
                <svg class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span>Processando...</span>
              </template>
              <template v-else>
                {{ confirmLabel }}
              </template>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-fade-enter-active {
  transition: opacity 0.3s ease-out;
}

.dialog-fade-leave-active {
  transition: opacity 0.25s ease-in;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
</style>
