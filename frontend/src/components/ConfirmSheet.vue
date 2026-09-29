<script setup>
import { watch } from "vue"
import Icon from "./Icon.vue"

const props = defineProps({
  open: Boolean,
  title: String,
  rows: { type: Array, default: () => [] },
  confirmText: { type: String, default: "Confirm" },
  note: String,
  busy: Boolean,
})
const emit = defineEmits(["update:open", "confirm"])
watch(() => props.open, (v) => { document.body.style.overflow = v ? "hidden" : "" })
</script>

<template>
  <teleport to="body">
    <transition name="sheet-fade">
      <div v-if="open" class="fixed inset-0 z-40 bg-black/40" @click="!busy && emit('update:open', false)"></div>
    </transition>
    <transition name="sheet-up">
      <div v-if="open" class="fixed inset-x-0 bottom-0 z-50 mx-auto flex max-h-[85vh] max-w-lg flex-col rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)] shadow-2xl">
        <div class="flex justify-center pt-2"><span class="h-1 w-10 rounded-full bg-gray-300"></span></div>
        <div class="px-4 pb-2 pt-3">
          <h2 class="text-base font-semibold">{{ title }}</h2>
          <p v-if="note" class="mt-1 flex items-start gap-1.5 text-xs text-amber-700"><Icon name="alert" :size="13" />{{ note }}</p>
        </div>
        <div class="flex-1 overflow-y-auto px-4">
          <dl class="divide-y divide-gray-100 rounded-lg border border-gray-200">
            <div v-for="r in rows.filter((x) => x.value)" :key="r.label" class="flex gap-3 px-3 py-2.5 text-sm">
              <dt class="w-28 shrink-0 text-gray-500">{{ r.label }}</dt>
              <dd class="min-w-0 flex-1 whitespace-pre-line break-words font-medium" dir="auto">{{ r.value }}</dd>
            </div>
          </dl>
        </div>
        <div class="grid grid-cols-2 gap-2 p-4">
          <button type="button" class="btn btn-subtle h-11" :disabled="busy" @click="emit('update:open', false)">Back</button>
          <button type="button" class="btn btn-primary h-11" :disabled="busy" @click="emit('confirm')">{{ busy ? "Saving…" : confirmText }}</button>
        </div>
      </div>
    </transition>
  </teleport>
</template>
