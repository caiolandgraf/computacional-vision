<script setup>
import { ref } from 'vue'

const props = defineProps({
  accept: {
    type: String,
    default: 'image/*',
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  maxSizeMb: {
    type: Number,
    default: 50,
  },
  label: {
    type: String,
    default: 'Arraste uma imagem aqui',
  },
  sublabel: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: '📁',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  preview: {
    type: String,
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['files', 'error', 'clear'])

const dragOver = ref(false)
const fileInputRef = ref(null)

function openFilePicker() {
  if (props.disabled) return
  fileInputRef.value?.click()
}

function onFileChange(event) {
  const selected = event.target.files
  if (!selected?.length) return
  processFiles(selected)
  // Reset input so the same file can be re-selected
  event.target.value = ''
}

function onDrop(event) {
  event.preventDefault()
  dragOver.value = false
  if (props.disabled) return

  const dropped = event.dataTransfer?.files
  if (!dropped?.length) return
  processFiles(dropped)
}

function onDragOver(event) {
  event.preventDefault()
  if (!props.disabled) {
    dragOver.value = true
  }
}

function onDragLeave() {
  dragOver.value = false
}

function processFiles(fileList) {
  const files = Array.from(fileList)

  // Validate accept types
  if (props.accept && props.accept !== '*') {
    const acceptPatterns = props.accept.split(',').map((a) => a.trim())

    const valid = files.filter((file) => {
      return acceptPatterns.some((pattern) => {
        if (pattern.endsWith('/*')) {
          const prefix = pattern.replace('/*', '')
          return file.type.startsWith(prefix)
        }
        if (pattern.startsWith('.')) {
          return file.name.toLowerCase().endsWith(pattern.toLowerCase())
        }
        return file.type === pattern
      })
    })

    if (valid.length === 0) {
      emit('error', `Tipo de arquivo não suportado. Aceitos: ${props.accept}`)
      return
    }

    if (valid.length < files.length) {
      emit('error', `${files.length - valid.length} arquivo(s) ignorado(s) por tipo inválido.`)
    }

    files.splice(0, files.length, ...valid)
  }

  // Validate size
  const maxBytes = props.maxSizeMb * 1024 * 1024
  const oversized = files.filter((f) => f.size > maxBytes)
  if (oversized.length > 0) {
    emit('error', `Arquivo(s) muito grande(s). Máximo: ${props.maxSizeMb}MB`)
    return
  }

  if (!props.multiple && files.length > 1) {
    emit('files', [files[0]])
  } else {
    emit('files', files)
  }
}

function clearFile() {
  emit('clear')
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

defineExpose({ openFilePicker })
</script>

<template>
  <!-- Preview mode: file already selected -->
  <div v-if="preview" class="relative group">
    <div class="relative overflow-hidden rounded-xl border border-surface-700/50 bg-surface-800/40">
      <img
        :src="preview"
        alt="Preview"
        class="w-full object-contain max-h-64 sm:max-h-80"
      />
      <!-- Overlay actions on hover -->
      <div
        class="absolute inset-0 bg-surface-950/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-3"
      >
        <button
          @click="openFilePicker"
          class="btn-secondary btn-sm"
          :disabled="disabled"
        >
          🔄 Trocar
        </button>
        <button
          @click="clearFile"
          class="btn-danger btn-sm"
          :disabled="disabled"
        >
          ✕ Remover
        </button>
      </div>
    </div>

    <!-- Hidden file input for swap -->
    <input
      ref="fileInputRef"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="hidden"
      @change="onFileChange"
    />
  </div>

  <!-- Slot for custom preview -->
  <div v-else-if="$slots.preview">
    <slot name="preview" :openFilePicker="openFilePicker" :clearFile="clearFile" />
    <input
      ref="fileInputRef"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="hidden"
      @change="onFileChange"
    />
  </div>

  <!-- Drop zone mode: no file selected yet -->
  <div
    v-else
    @click="openFilePicker"
    @drop="onDrop"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    :class="[
      'relative border-2 border-dashed rounded-xl transition-all duration-200 cursor-pointer group',
      'flex flex-col items-center justify-center text-center',
      compact ? 'p-4 gap-2' : 'p-6 sm:p-8 gap-3',
      disabled
        ? 'border-surface-700/30 bg-surface-800/20 opacity-50 cursor-not-allowed'
        : dragOver
          ? 'border-brand-500 bg-brand-500/10 scale-[1.01] shadow-lg shadow-brand-600/10'
          : 'border-surface-600/50 bg-surface-800/30 hover:border-surface-500 hover:bg-surface-800/50',
    ]"
  >
    <!-- Animated background blob on drag -->
    <div
      v-if="dragOver"
      class="absolute inset-0 pointer-events-none overflow-hidden rounded-xl"
    >
      <div class="absolute -inset-4 bg-brand-500/5 animate-pulse rounded-full blur-2xl" />
    </div>

    <!-- Icon -->
    <div
      :class="[
        'flex items-center justify-center rounded-xl transition-all duration-200',
        compact ? 'w-10 h-10 text-lg' : 'w-14 h-14 text-2xl',
        dragOver
          ? 'bg-brand-500/15 scale-110'
          : 'bg-surface-700/50 group-hover:bg-surface-700/70',
      ]"
    >
      {{ icon }}
    </div>

    <!-- Label -->
    <div class="relative">
      <p
        :class="[
          'font-semibold transition-colors',
          compact ? 'text-xs' : 'text-sm',
          dragOver ? 'text-brand-400' : 'text-surface-200 group-hover:text-white',
        ]"
      >
        {{ dragOver ? 'Solte para enviar' : label }}
      </p>
      <p
        v-if="sublabel && !dragOver"
        :class="[
          'text-surface-400 mt-0.5',
          compact ? 'text-[10px]' : 'text-xs',
        ]"
      >
        {{ sublabel }}
      </p>
      <p
        v-if="!compact"
        :class="[
          'text-surface-500 mt-1.5',
          compact ? 'text-[10px]' : 'text-xs',
        ]"
      >
        ou <span class="text-brand-400 font-medium underline underline-offset-2">clique para selecionar</span>
      </p>
    </div>

    <!-- Format hints -->
    <div v-if="!compact && !dragOver" class="flex items-center gap-2 flex-wrap justify-center mt-1">
      <span class="badge-surface text-[10px]">
        Máx {{ maxSizeMb }}MB
      </span>
      <span v-if="multiple" class="badge-surface text-[10px]">
        Múltiplos arquivos
      </span>
      <span v-if="accept && accept !== '*'" class="badge-surface text-[10px]">
        {{ accept.replace(/image\//g, '.').replace(/video\//g, '.').replace(/\*/g, 'todos') }}
      </span>
    </div>

    <!-- Slot for extra content below -->
    <slot />

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="hidden"
      @change="onFileChange"
    />
  </div>
</template>
