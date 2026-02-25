<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    default: '—',
  },
  icon: {
    type: String,
    default: '📊',
  },
  trend: {
    type: String,
    default: '',
    validator: (v) => ['', 'up', 'down', 'neutral'].includes(v),
  },
  trendValue: {
    type: String,
    default: '',
  },
  color: {
    type: String,
    default: 'brand',
    validator: (v) => ['brand', 'blue', 'purple', 'orange', 'red', 'yellow', 'teal', 'pink'].includes(v),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  subtitle: {
    type: String,
    default: '',
  },
  clickable: {
    type: Boolean,
    default: false,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Number,
    default: -1,
  },
})

defineEmits(['click'])

const colorMap = {
  brand: {
    iconBg: 'bg-brand-500/12',
    iconBorder: 'border-brand-500/15',
    iconText: 'text-brand-400',
    glow: 'shadow-brand-500/5',
    trendUp: 'text-brand-400',
    progressBar: 'bg-brand-500',
    accentRing: 'ring-brand-500/20',
  },
  blue: {
    iconBg: 'bg-blue-500/12',
    iconBorder: 'border-blue-500/15',
    iconText: 'text-blue-400',
    glow: 'shadow-blue-500/5',
    trendUp: 'text-blue-400',
    progressBar: 'bg-blue-500',
    accentRing: 'ring-blue-500/20',
  },
  purple: {
    iconBg: 'bg-purple-500/12',
    iconBorder: 'border-purple-500/15',
    iconText: 'text-purple-400',
    glow: 'shadow-purple-500/5',
    trendUp: 'text-purple-400',
    progressBar: 'bg-purple-500',
    accentRing: 'ring-purple-500/20',
  },
  orange: {
    iconBg: 'bg-orange-500/12',
    iconBorder: 'border-orange-500/15',
    iconText: 'text-orange-400',
    glow: 'shadow-orange-500/5',
    trendUp: 'text-orange-400',
    progressBar: 'bg-orange-500',
    accentRing: 'ring-orange-500/20',
  },
  red: {
    iconBg: 'bg-red-500/12',
    iconBorder: 'border-red-500/15',
    iconText: 'text-red-400',
    glow: 'shadow-red-500/5',
    trendUp: 'text-red-400',
    progressBar: 'bg-red-500',
    accentRing: 'ring-red-500/20',
  },
  yellow: {
    iconBg: 'bg-yellow-500/12',
    iconBorder: 'border-yellow-500/15',
    iconText: 'text-yellow-400',
    glow: 'shadow-yellow-500/5',
    trendUp: 'text-yellow-400',
    progressBar: 'bg-yellow-500',
    accentRing: 'ring-yellow-500/20',
  },
  teal: {
    iconBg: 'bg-teal-500/12',
    iconBorder: 'border-teal-500/15',
    iconText: 'text-teal-400',
    glow: 'shadow-teal-500/5',
    trendUp: 'text-teal-400',
    progressBar: 'bg-teal-500',
    accentRing: 'ring-teal-500/20',
  },
  pink: {
    iconBg: 'bg-pink-500/12',
    iconBorder: 'border-pink-500/15',
    iconText: 'text-pink-400',
    glow: 'shadow-pink-500/5',
    trendUp: 'text-pink-400',
    progressBar: 'bg-pink-500',
    accentRing: 'ring-pink-500/20',
  },
}

const colors = computed(() => colorMap[props.color] || colorMap.brand)

const trendIcon = computed(() => {
  if (props.trend === 'up') return '↑'
  if (props.trend === 'down') return '↓'
  if (props.trend === 'neutral') return '→'
  return ''
})

const trendColor = computed(() => {
  if (props.trend === 'up') return 'text-brand-400'
  if (props.trend === 'down') return 'text-red-400'
  if (props.trend === 'neutral') return 'text-surface-400'
  return 'text-surface-500'
})

const hasProgress = computed(() => props.progress >= 0 && props.progress <= 100)

const clampedProgress = computed(() => Math.min(100, Math.max(0, props.progress)))
</script>

<template>
  <component
    :is="clickable ? 'button' : 'div'"
    :class="[
      'relative overflow-hidden rounded-2xl border border-surface-700/50 bg-surface-800/60 backdrop-blur-sm',
      'shadow-xl shadow-black/10 transition-all duration-300 text-left',
      compact ? 'p-3.5' : 'p-5',
      clickable
        ? 'cursor-pointer hover:border-surface-600/60 hover:bg-surface-800/80 hover:shadow-2xl hover:shadow-black/20 active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900'
        : '',
      clickable ? colors.accentRing : '',
    ]"
    @click="clickable ? $emit('click') : undefined"
  >
    <!-- Subtle accent glow in top-right -->
    <div
      :class="[
        'absolute -top-8 -right-8 w-24 h-24 rounded-full blur-2xl pointer-events-none opacity-40 transition-opacity duration-500',
        colors.iconBg,
      ]"
    />

    <div class="relative flex items-start gap-3.5">
      <!-- Icon container -->
      <div
        :class="[
          'flex items-center justify-center rounded-xl border shrink-0 select-none transition-transform duration-300',
          compact ? 'w-10 h-10 text-lg' : 'w-12 h-12 text-xl',
          colors.iconBg,
          colors.iconBorder,
          clickable ? 'group-hover:scale-105' : '',
        ]"
      >
        <template v-if="loading">
          <svg
            :class="['animate-spin', compact ? 'w-4 h-4' : 'w-5 h-5', colors.iconText]"
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
        </template>
        <template v-else>
          {{ icon }}
        </template>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <!-- Label -->
        <p
          :class="[
            'font-medium text-surface-400 truncate leading-tight',
            compact ? 'text-[11px]' : 'text-xs',
          ]"
        >
          {{ label }}
        </p>

        <!-- Value -->
        <div class="flex items-baseline gap-2 mt-0.5">
          <template v-if="loading">
            <div
              :class="[
                'rounded-md bg-surface-700/60 animate-pulse',
                compact ? 'h-5 w-14' : 'h-7 w-20',
              ]"
            />
          </template>
          <template v-else>
            <p
              :class="[
                'font-bold tracking-tight text-white leading-none',
                compact ? 'text-lg' : 'text-2xl',
              ]"
            >
              {{ value }}
            </p>

            <!-- Trend indicator -->
            <span
              v-if="trend && trendValue"
              :class="[
                'inline-flex items-center gap-0.5 text-[10px] font-semibold leading-none',
                trendColor,
              ]"
            >
              <span class="text-[11px]">{{ trendIcon }}</span>
              {{ trendValue }}
            </span>
          </template>
        </div>

        <!-- Subtitle -->
        <p
          v-if="subtitle && !loading"
          :class="[
            'text-surface-500 truncate leading-tight',
            compact ? 'text-[10px] mt-0.5' : 'text-[11px] mt-1',
          ]"
        >
          {{ subtitle }}
        </p>
        <div
          v-else-if="loading && subtitle"
          :class="[
            'rounded bg-surface-700/40 animate-pulse',
            compact ? 'h-2.5 w-16 mt-1' : 'h-3 w-24 mt-1.5',
          ]"
        />

        <!-- Progress bar -->
        <div v-if="hasProgress && !loading" :class="['w-full', compact ? 'mt-2' : 'mt-2.5']">
          <div class="flex items-center justify-between mb-1">
            <div class="h-1.5 flex-1 bg-surface-700/60 rounded-full overflow-hidden">
              <div
                :class="[
                  'h-full rounded-full transition-all duration-700 ease-out',
                  colors.progressBar,
                ]"
                :style="{ width: clampedProgress + '%' }"
              />
            </div>
            <span class="text-[10px] font-mono text-surface-400 ml-2 tabular-nums">
              {{ Math.round(clampedProgress) }}%
            </span>
          </div>
        </div>

        <!-- Slot for custom content below -->
        <slot />
      </div>
    </div>

    <!-- Clickable arrow indicator -->
    <div
      v-if="clickable"
      class="absolute top-1/2 -translate-y-1/2 right-3 text-surface-600 transition-all duration-200"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </div>
  </component>
</template>
