<script setup>
import Icon from "./Icon.vue"
defineProps({ value: String, sub: String, placeholder: String, icon: { type: String, default: "search" } })
defineEmits(["open", "clear"])
</script>

<template>
  <div class="flex w-full items-center gap-2 rounded-lg border px-3 py-2"
    :class="value ? 'border-brand-200 bg-brand-50' : 'border-gray-200 bg-white'">
    <button type="button" class="flex min-w-0 flex-1 items-center gap-3 text-left" @click="$emit('open')">
      <Icon :name="icon" :size="16" :class="value ? 'text-brand-600' : 'text-gray-400'" />
      <span class="min-w-0 flex-1">
        <span v-if="value" class="block truncate font-medium" dir="auto">{{ value }}</span>
        <span v-else class="block truncate text-gray-400">{{ placeholder }}</span>
        <span v-if="value && sub" class="block truncate text-xs text-gray-500" dir="auto">{{ sub }}</span>
      </span>
      <Icon name="chevron-down" :size="16" class="text-gray-400" />
    </button>
    <button v-if="value" type="button" class="p-1 text-gray-400" aria-label="Clear" @click="$emit('clear')"><Icon name="x" :size="14" /></button>
  </div>
</template>
