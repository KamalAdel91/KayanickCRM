<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import Icon from "./components/Icon.vue"

const route = useRoute()
const showNav = computed(() => route.name !== "visit")
</script>

<template>
  <div class="min-h-screen" :class="showNav ? 'pb-20' : ''">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in"><component :is="Component" /></transition>
    </router-view>
    <nav v-if="showNav" class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="mx-auto flex max-w-lg">
        <router-link to="/" class="tab" :class="{ 'tab-on': route.name === 'today' }">
          <Icon name="home" :size="21" /><span>Today</span>
        </router-link>
        <router-link to="/visit" class="tab">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm shadow-brand-600/30"><Icon name="plus" :size="17" /></span>
          <span class="text-gray-900">New visit</span>
        </router-link>
        <router-link to="/search" class="tab" :class="{ 'tab-on': route.name === 'search' }">
          <Icon name="search" :size="21" /><span>Search</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>
