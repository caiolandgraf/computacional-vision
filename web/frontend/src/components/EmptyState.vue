<script setup>
defineProps({
  icon: {
    type: String,
    default: '📭',
  },
  title: {
    type: String,
    default: 'Nenhum item encontrado',
  },
  description: {
    type: String,
    default: '',
  },
  actionLabel: {
    type: String,
    default: '',
  },
  actionIcon: {
    type: String,
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['action'])
</script>

<template>
  <div
    :class="[
      'flex flex-col items-center justify-center text-center',
      compact ? 'py-8 px-4' : 'py-16 px-6',
    ]"
  >
    <!-- Icon -->
    <div
      :class="[
        'flex items-center justify-center rounded-2xl bg-surface-800/60 border border-surface-700/50',
        compact ? 'w-12 h-12 text-xl mb-3' : 'w-16 h-16 text-3xl mb-4',
      ]"
    >
      {{ icon }}
    </div>

    <!-- Title -->
    <h3
      :class="[
        'font-semibold text-surface-200',
        compact ? 'text-sm' : 'text-base',
      ]"
    >
      {{ title }}
    </h3>

    <!-- Description -->
    <p
      v-if="description"
      :class="[
        'text-surface-400 max-w-sm leading-relaxed',
        compact ? 'text-xs mt-1' : 'text-sm mt-2',
      ]"
    >
      {{ description }}
    </p>

    <!-- Slot for custom content -->
    <slot />

    <!-- Action button -->
    <button
      v-if="actionLabel"
      @click="$emit('action')"
      :class="[
        'btn-primary',
        compact ? 'btn-sm mt-3' : 'mt-5',
      ]"
    >
      <span v-if="actionIcon">{{ actionIcon }}</span>
      {{ actionLabel }}
    </button>
  </div>
</template>
