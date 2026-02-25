<script setup>
defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(v),
  },
  color: {
    type: String,
    default: 'brand',
    validator: (v) => ['brand', 'white', 'surface', 'red', 'blue', 'yellow'].includes(v),
  },
  label: {
    type: String,
    default: '',
  },
  overlay: {
    type: Boolean,
    default: false,
  },
  fullscreen: {
    type: Boolean,
    default: false,
  },
})

const sizeClasses = {
  xs: 'w-3.5 h-3.5',
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
}

const colorClasses = {
  brand: 'text-brand-500',
  white: 'text-white',
  surface: 'text-surface-400',
  red: 'text-red-500',
  blue: 'text-blue-500',
  yellow: 'text-yellow-500',
}

const labelSizeClasses = {
  xs: 'text-[10px]',
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg',
}
</script>

<template>
  <!-- Fullscreen overlay spinner -->
  <Teleport to="body" v-if="fullscreen">
    <Transition name="fade">
      <div class="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-surface-950/80 backdrop-blur-sm">
        <svg
          :class="['animate-spin', sizeClasses[size] || sizeClasses.lg, colorClasses[color]]"
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
        <p v-if="label" :class="['mt-4 font-medium', labelSizeClasses[size] || labelSizeClasses.lg, colorClasses[color]]">
          {{ label }}
        </p>
        <slot />
      </div>
    </Transition>
  </Teleport>

  <!-- Overlay spinner (covers parent container) -->
  <div
    v-else-if="overlay"
    class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-surface-900/60 backdrop-blur-[2px] rounded-2xl"
  >
    <svg
      :class="['animate-spin', sizeClasses[size] || sizeClasses.md, colorClasses[color]]"
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
    <p v-if="label" :class="['mt-3 font-medium', labelSizeClasses[size] || labelSizeClasses.md, 'text-surface-300']">
      {{ label }}
    </p>
    <slot />
  </div>

  <!-- Inline spinner -->
  <div v-else class="inline-flex flex-col items-center gap-2">
    <svg
      :class="['animate-spin', sizeClasses[size] || sizeClasses.md, colorClasses[color]]"
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
    <p v-if="label" :class="['font-medium', labelSizeClasses[size] || labelSizeClasses.sm, 'text-surface-400']">
      {{ label }}
    </p>
    <slot />
  </div>
</template>
