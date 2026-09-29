<script setup>
import { onBeforeUnmount } from "vue"
import Icon from "./Icon.vue"

const files = defineModel({ type: Array, default: () => [] })
let seq = 0

function add(e) {
  for (const file of e.target.files || []) {
    files.value.push({ id: ++seq, file, preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : "" })
  }
  e.target.value = ""
}
function remove(f) {
  if (f.preview) URL.revokeObjectURL(f.preview)
  files.value.splice(files.value.indexOf(f), 1)
}
function size(n) {
  return n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"
}
onBeforeUnmount(() => files.value.forEach((f) => f.preview && URL.revokeObjectURL(f.preview)))
</script>

<template>
  <div class="space-y-3">
    <div class="grid grid-cols-2 gap-2">
      <label class="btn btn-subtle cursor-pointer">
        <Icon name="camera" :size="16" />Camera
        <input type="file" accept="image/*" capture="environment" class="hidden" @change="add" />
      </label>
      <label class="btn btn-subtle cursor-pointer">
        <Icon name="paperclip" :size="16" />Files
        <input type="file" accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx" multiple class="hidden" @change="add" />
      </label>
    </div>
    <div v-if="files.length" class="divide-y divide-gray-100 rounded-lg border border-gray-200">
      <div v-for="f in files" :key="f.id" class="flex items-center gap-3 px-3 py-2">
        <img v-if="f.preview" :src="f.preview" class="h-10 w-10 shrink-0 rounded-md object-cover" alt="" />
        <span v-else class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500"><Icon name="file-text" :size="18" /></span>
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm">{{ f.file.name }}</span>
          <span class="block text-xs text-gray-400">{{ size(f.file.size) }}</span>
        </span>
        <button type="button" class="p-1 text-gray-400" aria-label="Remove" @click="remove(f)"><Icon name="x" :size="16" /></button>
      </div>
    </div>
  </div>
</template>
