<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Bar, Doughnut, Line, Radar } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  type: {
    type: String,
    default: 'bar',
    validator: (v) => ['bar', 'doughnut', 'line', 'radar'].includes(v),
  },
  title: {
    type: String,
    default: '',
  },
  labels: {
    type: Array,
    default: () => [],
  },
  datasets: {
    type: Array,
    default: () => [],
  },
  height: {
    type: [Number, String],
    default: 280,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  empty: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: 'Sem dados para exibir',
  },
  emptyIcon: {
    type: String,
    default: '📊',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  legendPosition: {
    type: String,
    default: 'bottom',
    validator: (v) => ['top', 'bottom', 'left', 'right', 'none'].includes(v),
  },
})

// ── Color palette matching Tailwind theme ────────────────────

const PALETTE = {
  brand: {
    bg: 'rgba(34, 197, 94, 0.15)',
    border: 'rgba(34, 197, 94, 0.8)',
    solid: 'rgba(34, 197, 94, 1)',
    gradient: ['rgba(34, 197, 94, 0.25)', 'rgba(34, 197, 94, 0.02)'],
  },
  blue: {
    bg: 'rgba(59, 130, 246, 0.15)',
    border: 'rgba(59, 130, 246, 0.8)',
    solid: 'rgba(59, 130, 246, 1)',
    gradient: ['rgba(59, 130, 246, 0.25)', 'rgba(59, 130, 246, 0.02)'],
  },
  purple: {
    bg: 'rgba(168, 85, 247, 0.15)',
    border: 'rgba(168, 85, 247, 0.8)',
    solid: 'rgba(168, 85, 247, 1)',
    gradient: ['rgba(168, 85, 247, 0.25)', 'rgba(168, 85, 247, 0.02)'],
  },
  orange: {
    bg: 'rgba(249, 115, 22, 0.15)',
    border: 'rgba(249, 115, 22, 0.8)',
    solid: 'rgba(249, 115, 22, 1)',
    gradient: ['rgba(249, 115, 22, 0.25)', 'rgba(249, 115, 22, 0.02)'],
  },
  red: {
    bg: 'rgba(239, 68, 68, 0.15)',
    border: 'rgba(239, 68, 68, 0.8)',
    solid: 'rgba(239, 68, 68, 1)',
    gradient: ['rgba(239, 68, 68, 0.25)', 'rgba(239, 68, 68, 0.02)'],
  },
  yellow: {
    bg: 'rgba(234, 179, 8, 0.15)',
    border: 'rgba(234, 179, 8, 0.8)',
    solid: 'rgba(234, 179, 8, 1)',
    gradient: ['rgba(234, 179, 8, 0.25)', 'rgba(234, 179, 8, 0.02)'],
  },
  teal: {
    bg: 'rgba(20, 184, 166, 0.15)',
    border: 'rgba(20, 184, 166, 0.8)',
    solid: 'rgba(20, 184, 166, 1)',
    gradient: ['rgba(20, 184, 166, 0.25)', 'rgba(20, 184, 166, 0.02)'],
  },
  pink: {
    bg: 'rgba(236, 72, 153, 0.15)',
    border: 'rgba(236, 72, 153, 0.8)',
    solid: 'rgba(236, 72, 153, 1)',
    gradient: ['rgba(236, 72, 153, 0.25)', 'rgba(236, 72, 153, 0.02)'],
  },
  cyan: {
    bg: 'rgba(6, 182, 212, 0.15)',
    border: 'rgba(6, 182, 212, 0.8)',
    solid: 'rgba(6, 182, 212, 1)',
    gradient: ['rgba(6, 182, 212, 0.25)', 'rgba(6, 182, 212, 0.02)'],
  },
}

const PALETTE_KEYS = Object.keys(PALETTE)

function getPaletteColor(index) {
  return PALETTE[PALETTE_KEYS[index % PALETTE_KEYS.length]]
}

// ── Shared chart styling ─────────────────────────────────────

const gridColor = 'rgba(51, 65, 85, 0.4)'
const tickColor = 'rgba(148, 163, 184, 0.7)'
const tooltipBg = 'rgba(15, 23, 42, 0.95)'
const tooltipBorder = 'rgba(51, 65, 85, 0.6)'
const tooltipTitle = 'rgba(226, 232, 240, 1)'
const tooltipBody = 'rgba(148, 163, 184, 1)'

const fontFamily = "'Inter', 'system-ui', '-apple-system', sans-serif"

// ── Build chartData from props ───────────────────────────────

const chartData = computed(() => {
  const builtDatasets = props.datasets.map((ds, i) => {
    const pal = ds.color ? (PALETTE[ds.color] || getPaletteColor(i)) : getPaletteColor(i)

    const base = {
      label: ds.label || `Dataset ${i + 1}`,
      data: ds.data || [],
    }

    if (props.type === 'bar') {
      return {
        ...base,
        backgroundColor: ds.backgroundColor || pal.bg,
        borderColor: ds.borderColor || pal.border,
        borderWidth: ds.borderWidth ?? 1.5,
        borderRadius: ds.borderRadius ?? 6,
        borderSkipped: false,
        hoverBackgroundColor: ds.hoverBackgroundColor || pal.border,
        hoverBorderColor: ds.hoverBorderColor || pal.solid,
        barThickness: ds.barThickness,
        maxBarThickness: ds.maxBarThickness ?? 48,
        categoryPercentage: ds.categoryPercentage,
        barPercentage: ds.barPercentage,
      }
    }

    if (props.type === 'line') {
      return {
        ...base,
        borderColor: ds.borderColor || pal.border,
        backgroundColor: ds.fill !== false ? (ds.backgroundColor || pal.gradient[0]) : 'transparent',
        borderWidth: ds.borderWidth ?? 2,
        pointRadius: ds.pointRadius ?? 3,
        pointHoverRadius: ds.pointHoverRadius ?? 6,
        pointBackgroundColor: ds.pointBackgroundColor || pal.solid,
        pointBorderColor: ds.pointBorderColor || pal.solid,
        pointHoverBackgroundColor: ds.pointHoverBackgroundColor || '#fff',
        pointHoverBorderColor: ds.pointHoverBorderColor || pal.solid,
        pointBorderWidth: ds.pointBorderWidth ?? 2,
        pointHoverBorderWidth: ds.pointHoverBorderWidth ?? 3,
        tension: ds.tension ?? 0.35,
        fill: ds.fill !== false ? 'origin' : false,
        segment: ds.segment,
      }
    }

    if (props.type === 'doughnut') {
      const bgColors = ds.backgroundColor || ds.data.map((_, j) => getPaletteColor(j).bg)
      const borderColors = ds.borderColor || ds.data.map((_, j) => getPaletteColor(j).border)
      const hoverBgColors = ds.hoverBackgroundColor || ds.data.map((_, j) => getPaletteColor(j).border)

      return {
        ...base,
        backgroundColor: bgColors,
        borderColor: borderColors,
        hoverBackgroundColor: hoverBgColors,
        borderWidth: ds.borderWidth ?? 2,
        hoverBorderWidth: ds.hoverBorderWidth ?? 3,
        spacing: ds.spacing ?? 2,
        cutout: ds.cutout,
      }
    }

    if (props.type === 'radar') {
      return {
        ...base,
        borderColor: ds.borderColor || pal.border,
        backgroundColor: ds.backgroundColor || pal.bg,
        borderWidth: ds.borderWidth ?? 2,
        pointRadius: ds.pointRadius ?? 3,
        pointHoverRadius: ds.pointHoverRadius ?? 6,
        pointBackgroundColor: ds.pointBackgroundColor || pal.solid,
        pointBorderColor: ds.pointBorderColor || pal.solid,
        pointHoverBackgroundColor: ds.pointHoverBackgroundColor || '#fff',
        pointHoverBorderColor: ds.pointHoverBorderColor || pal.solid,
        fill: ds.fill !== false,
      }
    }

    return base
  })

  return {
    labels: props.labels,
    datasets: builtDatasets,
  }
})

// ── Chart options ────────────────────────────────────────────

const chartOptions = computed(() => {
  const showLegend = props.legendPosition !== 'none' && props.datasets.length > 1

  const base = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    animation: {
      duration: 600,
      easing: 'easeOutQuart',
    },
    plugins: {
      legend: {
        display: showLegend,
        position: props.legendPosition === 'none' ? 'bottom' : props.legendPosition,
        labels: {
          color: tickColor,
          font: {
            family: fontFamily,
            size: props.compact ? 10 : 11,
            weight: 500,
          },
          padding: props.compact ? 10 : 14,
          usePointStyle: true,
          pointStyle: 'circle',
          boxWidth: props.compact ? 6 : 8,
          boxHeight: props.compact ? 6 : 8,
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: tooltipBg,
        borderColor: tooltipBorder,
        borderWidth: 1,
        titleColor: tooltipTitle,
        bodyColor: tooltipBody,
        titleFont: {
          family: fontFamily,
          size: 12,
          weight: 600,
        },
        bodyFont: {
          family: fontFamily,
          size: 11,
          weight: 400,
        },
        padding: { x: 12, y: 8 },
        cornerRadius: 10,
        boxPadding: 4,
        usePointStyle: true,
        caretSize: 0,
        displayColors: true,
      },
      title: {
        display: false,
      },
    },
  }

  if (props.type === 'bar') {
    return {
      ...base,
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: tickColor,
            font: {
              family: fontFamily,
              size: props.compact ? 9 : 11,
              weight: 500,
            },
            padding: 4,
            maxRotation: 45,
            autoSkip: true,
            autoSkipPadding: 8,
          },
          border: {
            display: false,
          },
        },
        y: {
          grid: {
            color: gridColor,
            drawBorder: false,
            lineWidth: 0.8,
          },
          ticks: {
            color: tickColor,
            font: {
              family: fontFamily,
              size: props.compact ? 9 : 11,
              weight: 500,
            },
            padding: 8,
            maxTicksLimit: props.compact ? 4 : 6,
          },
          border: {
            display: false,
          },
          beginAtZero: true,
        },
      },
    }
  }

  if (props.type === 'line') {
    return {
      ...base,
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: tickColor,
            font: {
              family: fontFamily,
              size: props.compact ? 9 : 11,
              weight: 500,
            },
            padding: 4,
            maxRotation: 0,
            autoSkip: true,
            autoSkipPadding: 12,
          },
          border: {
            display: false,
          },
        },
        y: {
          grid: {
            color: gridColor,
            drawBorder: false,
            lineWidth: 0.8,
          },
          ticks: {
            color: tickColor,
            font: {
              family: fontFamily,
              size: props.compact ? 9 : 11,
              weight: 500,
            },
            padding: 8,
            maxTicksLimit: props.compact ? 4 : 6,
          },
          border: {
            display: false,
          },
          beginAtZero: true,
        },
      },
    }
  }

  if (props.type === 'doughnut') {
    return {
      ...base,
      cutout: '68%',
      plugins: {
        ...base.plugins,
        legend: {
          ...base.plugins.legend,
          display: true,
          position: props.legendPosition === 'none' ? 'bottom' : props.legendPosition,
        },
      },
    }
  }

  if (props.type === 'radar') {
    return {
      ...base,
      scales: {
        r: {
          angleLines: {
            color: gridColor,
            lineWidth: 0.8,
          },
          grid: {
            color: gridColor,
            lineWidth: 0.8,
          },
          pointLabels: {
            color: tickColor,
            font: {
              family: fontFamily,
              size: props.compact ? 9 : 11,
              weight: 500,
            },
          },
          ticks: {
            color: tickColor,
            backdropColor: 'transparent',
            font: {
              family: fontFamily,
              size: 9,
              weight: 400,
            },
            stepSize: undefined,
            maxTicksLimit: 5,
          },
          beginAtZero: true,
        },
      },
    }
  }

  return base
})

// ── Component map ────────────────────────────────────────────

const componentMap = {
  bar: Bar,
  doughnut: Doughnut,
  line: Line,
  radar: Radar,
}

const chartComponent = computed(() => componentMap[props.type] || Bar)

const heightPx = computed(() => {
  const h = typeof props.height === 'number' ? props.height : parseInt(props.height, 10) || 280
  return `${h}px`
})

const hasData = computed(() => {
  if (props.empty) return false
  if (!props.datasets || props.datasets.length === 0) return false
  return props.datasets.some((ds) => ds.data && ds.data.length > 0)
})
</script>

<template>
  <div class="card overflow-hidden">
    <!-- Header -->
    <div
      v-if="title || $slots.header || $slots.actions"
      :class="[
        'flex items-center justify-between gap-3 border-b border-surface-700/40',
        compact ? 'px-4 py-3' : 'px-5 py-4',
      ]"
    >
      <div class="flex items-center gap-2.5 min-w-0">
        <slot name="header">
          <h3
            :class="[
              'font-semibold text-surface-200 truncate',
              compact ? 'text-xs' : 'text-sm',
            ]"
          >
            {{ title }}
          </h3>
        </slot>
      </div>
      <div v-if="$slots.actions" class="shrink-0">
        <slot name="actions" />
      </div>
    </div>

    <!-- Chart body -->
    <div :class="compact ? 'p-3' : 'p-4 sm:p-5'">
      <!-- Loading skeleton -->
      <div
        v-if="loading"
        class="flex items-center justify-center"
        :style="{ height: heightPx }"
      >
        <div class="flex flex-col items-center gap-3">
          <svg
            class="animate-spin w-8 h-8 text-surface-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="3"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p class="text-xs text-surface-500 font-medium">Carregando dados...</p>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!hasData"
        class="flex flex-col items-center justify-center text-center"
        :style="{ height: heightPx }"
      >
        <div class="w-12 h-12 flex items-center justify-center rounded-xl bg-surface-800/60 border border-surface-700/50 text-2xl mb-3">
          {{ emptyIcon }}
        </div>
        <p class="text-sm font-medium text-surface-400">{{ emptyText }}</p>
        <p class="text-xs text-surface-500 mt-1">
          Realize análises para ver os dados aqui
        </p>
      </div>

      <!-- Chart canvas -->
      <div v-else :style="{ height: heightPx }" class="relative">
        <component
          :is="chartComponent"
          :data="chartData"
          :options="chartOptions"
        />
      </div>

      <!-- Footer slot for stats / summary below chart -->
      <div v-if="$slots.footer" :class="['border-t border-surface-700/30', compact ? 'mt-3 pt-3' : 'mt-4 pt-4']">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
