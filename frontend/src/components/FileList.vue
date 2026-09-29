<script setup>
import Icon from "./Icon.vue"

defineProps({ files: { type: Array, default: () => [] } })
const isImage = (f) => /\.(jpe?g|png|gif|webp|heic)$/i.test(f.file_name || f.file_url || "")
function size(n) {
  if (!n) return ""
  return n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"
}
</script>

<template>
  <p v-if="!files.length" class="py-2 text-center text-sm text-gray-400">No attachments</p>
  <div v-else class="divide-y divide-gray-100 rounded-lg border border-gray-200">
    <a v-for="f in files" :key="f.name" :href="f.file_url" target="_blank" rel="noopener" class="flex items-center gap-3 px-3 py-2 active:bg-gray-50">
      <img v-if="isImage(f)" :src="f.file_url" class="h-10 w-10 shrink-0 rounded-md object-cover" alt="" loading="lazy" />
      <span v-else class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500"><Icon name="file-text" :size="18" /></span>
      <span class="min-w-0 flex-1">
        <span class="block truncate text-sm">{{ f.file_name }}</span>
        <span class="block text-xs text-gray-400">{{ size(f.file_size) }}</span>
      </span>
      <Icon name="chevron-right" :size="16" class="text-gray-300" />
    </a>
  </div>
</template>
