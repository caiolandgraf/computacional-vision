<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
    // Each option: { value, label, description?, icon?, disabled?, badge?, badgeColor? }
  },
  label: {
    type: String,
    default: '',
  },
  columns: {
    type: Number,
    default: 0, // 0 = auto
  },
  compact: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    default: () => `method-${Math.random().toString(36).slice(2, 8)}`,
  },
  vertical: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const selectedOption = computed(() =>
  props.options.find((o) => o.value === props.modelValue) || null
)

function select(value) {
  if (props.disabled) return
  const opt = props.options.find((o) => o.value === value)
  if (opt?.disabled) return
  emit('update:modelValue', value)
}

function isSelected(value) {
  return props.modelValue === value
}

const gridClass = computed(() => {
  if (props.vertical) return 'flex flex-col gap-2'
  if (props.columns > 0) {
    const map = {
      1: 'grid grid-cols-1 gap-2',
      2: 'grid grid-cols-1 sm:grid-cols-2 gap-2',
      3: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2',
      4: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2',
    }
    return map[props.columns] || `grid grid-cols-${props.columns} gap-2`
  }
  // Auto: adapt to count
  const count = props.options.length
  if (count <= 2) return 'grid grid-cols-1 sm:grid-cols-2 gap-2'
  if (count <= 3) return 'grid grid-cols-1 sm:grid-cols-3 gap-2'
  return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2'
})

const badgeColorMap = {
  brand: 'bg-brand-500/15 text-brand-400 ring-1 ring-brand-500/20',
  blue: 'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20',
  purple: 'bg-purple-500/15 text-purple-400 ring-1 ring-purple-500/20',
  orange: 'bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/20',
  red: 'bg-red-500/15 text-red-400 ring-1 ring-red-500/20',
  yellow: 'bg-yellow-500/15 text-yellow-400 ring-1 ring-yellow-500/20',
  teal: 'bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/20',
  surface: 'bg-surface-700 text-surface-300 ring-1 ring-surface-600',
}
</script>

<template>
  <div>
    <!-- Label -->
    <label
      v-if="label"
      :class="[
        'block font-medium text-surface-300 mb-2',
        compact ? 'text-xs' : 'text-sm',
      ]"
    >
      {{ label }}
    </label>

    <!-- Options grid -->
    <div :class="gridClass" role="radiogroup" :aria-label="label">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        role="radio"
        :aria-checked="isSelected(option.value)"
        :aria-label="option.label"
        :disabled="disabled || option.disabled"
        @click="select(option.value)"
        :class="[
          'relative text-left rounded-xl border transition-all duration-200 group',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900',
          compact ? 'p-3' : 'p-3.5 sm:p-4',
          disabled || option.disabled
            ? 'opacity-40 cursor-not-allowed border-surface-700/30 bg-surface-800/20'
            : isSelected(option.value)
              ? 'border-brand-500/50 bg-brand-500/8 shadow-sm shadow-brand-600/5'
              : 'border-surface-700/50 bg-surface-800/40 hover:border-surface-600/60 hover:bg-surface-800/60 cursor-pointer',
        ]"
      >
        <!-- Active left indicator bar -->
        <div
          v-if="isSelected(option.value)"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 bg-brand-500 rounded-r-full transition-all duration-200"
        />

        <div class="flex items-start gap-3">
          <!-- Radio circle -->
          <div
            :class="[
              'shrink-0 mt-0.5 flex items-center justify-center rounded-full border-2 transition-all duration-200',
              compact ? 'w-4 h-4' : 'w-[18px] h-[18px]',
              isSelected(option.value)
                ? 'border-brand-500 bg-brand-500'
                : 'border-surface-500 bg-transparent group-hover:border-surface-400',
            ]"
          >
            <Transition name="scale">
              <div
                v-if="isSelected(option.value)"
                :class="[
                  'rounded-full bg-white',
                  compact ? 'w-1.5 h-1.5' : 'w-[7px] h-[7px]',
                ]"
              />
            </Transition>
          </div>

          <!-- Icon (optional) -->
          <span
            v-if="option.icon"
            :class="[
              'shrink-0 select-none transition-transform duration-200',
              compact ? 'text-base' : 'text-lg',
              isSelected(option.value) ? 'scale-110' : 'scale-100',
            ]"
          >
            {{ option.icon }}
          </span>

          <!-- Text content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p
                :class="[
                  'font-semibold leading-tight truncate transition-colors duration-200',
                  compact ? 'text-xs' : 'text-sm',
                  isSelected(option.value)
                    ? 'text-brand-400'
                    : 'text-surface-200 group-hover:text-white',
                ]"
              >
                {{ option.label }}
              </p>
              <span
                v-if="option.badge"
                :class="[
                  'inline-flex items-center px-1.5 py-px rounded-full font-semibold shrink-0',
                  compact ? 'text-[8px]' : 'text-[9px]',
                  badgeColorMap[option.badgeColor || 'brand'] || badgeColorMap.brand,
                ]"
              >
                {{ option.badge }}
              </span>
            </div>
            <p
              v-if="option.description && !compact"
              :class="[
                'text-xs leading-relaxed mt-0.5 transition-colors duration-200',
                isSelected(option.value)
                  ? 'text-surface-400'
                  : 'text-surface-500 group-hover:text-surface-400',
              ]"
            >
              {{ option.description }}
            </p>
          </div>

          <!-- Checkmark for selected -->
          <Transition name="scale">
            <div
              v-if="isSelected(option.value)"
              :class="[
                'shrink-0 flex items-center justify-center rounded-lg bg-brand-500/15 text-brand-400',
                compact ? 'w-5 h-5' : 'w-6 h-6',
              ]"
            >
              <svg
                :class="compact ? 'w-3 h-3' : 'w-3.5 h-3.5'"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="3"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </Transition>
        </div>
      </button>
    </div>

    <!-- Selected summary slot -->
    <slot name="summary" :selected="selectedOption" />
  </div>
</template>

<style scoped>
.scale-enter-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.scale-leave-active {
  transition: all 0.15s ease-in;
}

.scale-enter-from {
  opacity: 0;
  transform: scale(0.3);
}

.scale-leave-to {
  opacity: 0;
  transform: scale(0.5);
}
</style>
