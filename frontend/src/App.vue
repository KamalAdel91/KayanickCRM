<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import Icon from "./components/Icon.vue"
import InstallPrompt from "./components/InstallPrompt.vue"

const route = useRoute()
const showNav = computed(() => !["visit", "case"].includes(route.name))
</script>

<template>
  <div class="min-h-screen" :class="showNav ? 'pb-20' : ''">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in"><component :is="Component" /></transition>
    </router-view>
    <InstallPrompt v-if="showNav" />
    <nav v-if="showNav" class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="mx-auto flex max-w-lg">
        <router-link to="/" class="tab" :class="{ 'tab-on': route.name === 'today' }">
          <Icon name="home" :size="21" /><span>Today</span>
        </router-link>
        <router-link to="/visits" class="tab" :class="{ 'tab-on': ['visits', 'visit-detail'].includes(route.name) }">
          <Icon name="clipboard" :size="21" /><span>Visits</span>
        </router-link>
        <router-link to="/cases" class="tab" :class="{ 'tab-on': ['cases', 'case-detail'].includes(route.name) }">
          <Icon name="cart" :size="21" /><span>Cases</span>
        </router-link>
        <router-link to="/search" class="tab" :class="{ 'tab-on': route.name === 'search' }">
          <Icon name="search" :size="21" /><span>Search</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>
