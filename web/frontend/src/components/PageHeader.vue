<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: '',
  },
  badge: {
    type: String,
    default: '',
  },
  badgeColor: {
    type: String,
    default: 'brand',
    validator: (v) => ['brand', 'blue', 'purple', 'orange', 'red', 'yellow', 'teal', 'pink', 'surface'].includes(v),
  },
  compact: {
    type: Boolean,
    default: false,
  },
  gradient: {
    type: Boolean,
    default: false,
  },
  backRoute: {
    type: [String, Object],
    default: '',
  },
})

defineEmits(['back'])

const badgeColorMap = {
  brand: 'bg-brand-500/15 text-brand-400 ring-1 ring-brand-500/20',
  blue: 'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20',
  purple: 'bg-purple-500/15 text-purple-400 ring-1 ring-purple-500/20',
  orange: 'bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/20',
  red: 'bg-red-500/15 text-red-400 ring-1 ring-red-500/20',
  yellow: 'bg-yellow-500/15 text-yellow-400 ring-1 ring-yellow-500/20',
  teal: 'bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/20',
  pink: 'bg-pink-500/15 text-pink-400 ring-1 ring-pink-500/20',
  surface: 'bg-surface-700 text-surface-300 ring-1 ring-surface-600',
}
</script>

<template>
  <div
    :class="[
      'relative',
      compact ? 'mb-4' : 'mb-6 sm:mb-8',
    ]"
  >
    <!-- Gradient card background variant -->
    <div
      v-if="gradient"
      :class="[
        'relative overflow-hidden rounded-2xl border border-surface-700/50 bg-surface-800/60 backdrop-blur-sm shadow-xl shadow-black/10',
        compact ? 'p-4 sm:p-5' : 'p-5 sm:p-7',
      ]"
    >
      <!-- Decorative blobs -->
      <div class="absolute inset-0 bg-gradient-to-br from-brand-600/8 via-transparent to-emerald-600/4 pointer-events-none" />
      <div class="absolute top-0 right-0 w-48 h-48 bg-brand-500/5 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/4" />
      <div class="absolute bottom-0 left-0 w-32 h-32 bg-emerald-500/4 rounded-full blur-2xl pointer-events-none translate-y-1/2 -translate-x-1/4" />

      <div class="relative flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div class="flex items-start gap-3.5 min-w-0">
          <!-- Back button -->
          <button
            v-if="backRoute"
            @click="$emit('back')"
            class="shrink-0 mt-0.5 p-1.5 -ml-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/60 transition-colors"
            title="Voltar"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Icon -->
          <div
            v-if="icon"
            :class="[
              'shrink-0 flex items-center justify-center rounded-xl bg-brand-500/10 border border-brand-500/15',
              compact ? 'w-10 h-10 text-lg' : 'w-12 h-12 text-xl',
            ]"
          >
            {{ icon }}
          </div>

          <div class="min-w-0">
            <div class="flex items-center gap-2.5 flex-wrap">
              <h1
                :class="[
                  'font-extrabold tracking-tight text-white leading-tight',
                  compact ? 'text-lg sm:text-xl' : 'text-xl sm:text-2xl',
                ]"
              >
                {{ title }}
              </h1>
              <span
                v-if="badge"
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
                  badgeColorMap[badgeColor] || badgeColorMap.brand,
                ]"
              >
                {{ badge }}
              </span>
            </div>
            <p
              v-if="description"
              :class="[
                'text-surface-400 leading-relaxed max-w-2xl',
                compact ? 'text-xs mt-1' : 'text-sm mt-1.5',
              ]"
            >
              {{ description }}
            </p>
            <!-- Extra content slot below description -->
            <div v-if="$slots.subtitle" :class="compact ? 'mt-2' : 'mt-3'">
              <slot name="subtitle" />
            </div>
          </div>
        </div>

        <!-- Right-side actions -->
        <div v-if="$slots.actions" class="shrink-0 flex items-center gap-2 flex-wrap sm:mt-0.5">
          <slot name="actions" />
        </div>
      </div>

      <!-- Bottom slot for tabs, filters etc. -->
      <div v-if="$slots.bottom" class="relative mt-4 pt-4 border-t border-surface-700/40">
        <slot name="bottom" />
      </div>
    </div>

    <!-- Simple flat header variant (no gradient card) -->
    <div v-else>
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div class="flex items-start gap-3 min-w-0">
          <!-- Back button -->
          <button
            v-if="backRoute"
            @click="$emit('back')"
            class="shrink-0 mt-0.5 p-1.5 -ml-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/60 transition-colors"
            title="Voltar"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Icon -->
          <span
            v-if="icon"
            :class="compact ? 'text-lg mt-0.5' : 'text-xl mt-0.5'"
          >
            {{ icon }}
          </span>

          <div class="min-w-0">
            <div class="flex items-center gap-2.5 flex-wrap">
              <h1
                :class="[
                  'font-bold tracking-tight text-white leading-tight',
                  compact ? 'text-base sm:text-lg' : 'text-lg sm:text-xl',
                ]"
              >
                {{ title }}
              </h1>
              <span
                v-if="badge"
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold',
                  badgeColorMap[badgeColor] || badgeColorMap.brand,
                ]"
              >
                {{ badge }}
              </span>
            </div>
            <p
              v-if="description"
              :class="[
                'text-surface-400 leading-relaxed max-w-2xl',
                compact ? 'text-xs mt-0.5' : 'text-sm mt-1',
              ]"
            >
              {{ description }}
            </p>
            <div v-if="$slots.subtitle" :class="compact ? 'mt-1.5' : 'mt-2'">
              <slot name="subtitle" />
            </div>
          </div>
        </div>

        <!-- Right-side actions -->
        <div v-if="$slots.actions" class="shrink-0 flex items-center gap-2 flex-wrap">
          <slot name="actions" />
        </div>
      </div>

      <!-- Divider -->
      <div :class="['border-t border-surface-700/40', compact ? 'mt-3' : 'mt-4']" />

      <!-- Bottom slot -->
      <div v-if="$slots.bottom" :class="compact ? 'mt-3' : 'mt-4'">
        <slot name="bottom" />
      </div>
    </div>
  </div>
</template>
