<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { routes } from './router'
import ToastNotification from './components/ToastNotification.vue'
import ConnectionStatus from './components/ConnectionStatus.vue'

const router = useRouter()
const route = useRoute()

const sidebarOpen = ref(true)
const mobileMenuOpen = ref(false)

const navItems = computed(() =>
  routes
    .filter(r => r.name && r.name !== 'NotFound')
    .map(r => ({
      name: r.name,
      path: r.path,
      title: r.meta?.title || r.name,
      icon: r.meta?.icon || '📄'
    }))
)

const currentTitle = computed(() => {
  const current = navItems.value.find(item => item.path === route.path)
  return current?.title || 'Dashboard'
})

const currentIcon = computed(() => {
  const current = navItems.value.find(item => item.path === route.path)
  return current?.icon || '📊'
})

function navigateTo(path) {
  router.push(path)
  mobileMenuOpen.value = false
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function isActive(path) {
  return route.path === path
}
</script>

<template>
  <ToastNotification />
  <!-- Connection status monitors backend health globally -->
  <div class="flex h-screen overflow-hidden">
    <!-- Mobile overlay -->
    <Transition name="fade">
      <div
        v-if="mobileMenuOpen"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
        @click="mobileMenuOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-50 flex flex-col',
        'bg-surface-900/95 backdrop-blur-xl border-r border-surface-700/50',
        'transition-all duration-300 ease-out',
        sidebarOpen ? 'w-64' : 'w-[72px]',
        mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <!-- Logo area -->
      <div
        class="flex items-center h-16 px-4 border-b border-surface-700/50 shrink-0"
      >
        <div class="flex items-center gap-3 overflow-hidden">
          <div
            class="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-emerald-600 flex items-center justify-center text-lg shadow-lg shadow-brand-600/20 shrink-0"
          >
            🌿
          </div>
          <Transition name="fade">
            <div v-if="sidebarOpen" class="min-w-0">
              <h1 class="text-sm font-bold text-white truncate leading-tight">
                Visão Computacional
              </h1>
              <p class="text-[10px] text-surface-400 truncate">
                Sistema de Detecção
              </p>
            </div>
          </Transition>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto py-3 px-2.5 space-y-0.5">
        <button
          v-for="item in navItems"
          :key="item.path"
          @click="navigateTo(item.path)"
          :class="[
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium',
            'transition-all duration-200 group relative',
            isActive(item.path)
              ? 'bg-brand-600/15 text-brand-400 shadow-sm shadow-brand-600/5'
              : 'text-surface-400 hover:text-white hover:bg-surface-800/80'
          ]"
        >
          <!-- Active indicator -->
          <div
            v-if="isActive(item.path)"
            class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-brand-500 rounded-r-full"
          />

          <span class="text-base shrink-0 w-6 text-center">{{
            item.icon
          }}</span>

          <Transition name="fade">
            <span v-if="sidebarOpen" class="truncate">{{ item.title }}</span>
          </Transition>

          <!-- Tooltip when collapsed -->
          <div
            v-if="!sidebarOpen"
            class="absolute left-full ml-2 px-2.5 py-1 bg-surface-800 border border-surface-700 rounded-lg text-xs text-white whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 shadow-xl"
          >
            {{ item.title }}
          </div>
        </button>
      </nav>

      <!-- Sidebar footer -->
      <div class="border-t border-surface-700/50 p-2.5 shrink-0">
        <button
          @click="toggleSidebar"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-surface-400 hover:text-white hover:bg-surface-800/80 transition-all duration-200 text-sm"
        >
          <svg
            :class="[
              'w-4 h-4 transition-transform duration-300',
              !sidebarOpen && 'rotate-180'
            ]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
          <Transition name="fade">
            <span v-if="sidebarOpen" class="text-xs">Recolher</span>
          </Transition>
        </button>
      </div>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Top bar -->
      <header
        class="h-16 flex items-center justify-between px-4 sm:px-6 border-b border-surface-700/50 bg-surface-900/50 backdrop-blur-sm shrink-0 z-30"
      >
        <div class="flex items-center gap-3">
          <!-- Mobile menu button -->
          <button
            class="lg:hidden p-2 -ml-2 rounded-lg text-surface-400 hover:text-white hover:bg-surface-800 transition-colors"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          <div class="flex items-center gap-2.5">
            <span class="text-lg">{{ currentIcon }}</span>
            <h2 class="text-base font-semibold text-white">
              {{ currentTitle }}
            </h2>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Live backend status indicator -->
          <div class="hidden sm:block relative">
            <ConnectionStatus compact :interval="30000" auto-hide />
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto">
        <div class="p-4 sm:p-6 lg:p-8 max-w-[1600px] mx-auto">
          <router-view v-slot="{ Component }">
            <Transition name="slide" mode="out-in">
              <component :is="Component" />
            </Transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>
