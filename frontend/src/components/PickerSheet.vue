<script setup>
import { ref, watch, nextTick } from "vue"
import Icon from "./Icon.vue"

const props = defineProps({
  open: Boolean,
  title: String,
  fetcher: Function,
  multi: Boolean,
  selected: { type: Array, default: () => [] },
  placeholder: { type: String, default: "Search" },
  createLabel: String,
})
const emit = defineEmits(["update:open", "pick", "create"])
const q = ref("")
const rows = ref([])
const loading = ref(false)
const error = ref("")
const input = ref(null)
let timer = null
let token = 0

async function load() {
  const t = ++token
  loading.value = true
  error.value = ""
  try {
    const r = await props.fetcher(q.value)
    if (t === token) rows.value = r || []
  } catch (e) {
    if (t === token) error.value = e.message
  } finally {
    if (t === token) loading.value = false
  }
}
watch(() => props.open, async (v) => {
  document.body.style.overflow = v ? "hidden" : ""
  if (!v) return
  q.value = ""
  load()
  await nextTick()
  if (window.innerWidth > 640 && input.value) input.value.focus()
})
watch(q, () => { clearTimeout(timer); timer = setTimeout(load, 250) })
function pick(r) {
  emit("pick", r)
  if (!props.multi) emit("update:open", false)
}
function close() { emit("update:open", false) }
function create() {
  emit("create", q.value.trim())
  emit("update:open", false)
}
</script>

<template>
  <teleport to="body">
    <transition name="sheet-fade">
      <div v-if="open" class="fixed inset-0 z-40 bg-black/40" @click="close"></div>
    </transition>
    <transition name="sheet-up">
      <div v-if="open" class="fixed inset-x-0 bottom-0 z-50 mx-auto flex h-[85vh] max-w-lg flex-col rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)] shadow-2xl">
        <div class="flex justify-center pt-2"><span class="h-1 w-10 rounded-full bg-gray-300"></span></div>
        <div class="flex items-center gap-3 px-4 pb-2 pt-2">
          <h2 class="flex-1 text-base font-semibold">{{ title }}</h2>
          <button type="button" class="btn" :class="multi ? 'btn-primary' : 'btn-subtle w-9 px-0'" @click="close">
            <template v-if="multi">Done<span v-if="selected.length"> ({{ selected.length }})</span></template>
            <Icon v-else name="x" :size="16" />
          </button>
        </div>
        <div class="px-4 pb-3">
          <div class="relative">
            <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
            <input ref="input" v-model="q" type="search" :placeholder="placeholder" class="input pl-9" dir="auto" />
          </div>
        </div>
        <div class="flex-1 overflow-y-auto border-t border-gray-100">
          <p v-if="error" class="m-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
          <p v-else-if="loading && !rows.length" class="p-6 text-center text-sm text-gray-400">Loading…</p>
          <p v-else-if="!rows.length" class="p-6 text-center text-sm text-gray-400">Nothing found</p>
          <button v-for="r in rows" :key="r.value" type="button"
            class="flex w-full items-center gap-3 border-b border-gray-50 px-4 py-3 text-left active:bg-gray-50" @click="pick(r)">
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ r.label }}</span>
              <span v-if="r.sub" class="block truncate text-xs text-gray-500" dir="auto">{{ r.sub }}</span>
            </span>
            <span v-if="selected.includes(r.value)" class="badge badge-blue"><Icon name="check" :size="12" />Added</span>
            <Icon v-else :name="multi ? 'plus' : 'chevron-right'" :size="16" class="text-gray-300" />
          </button>
          <button v-if="createLabel && q.trim()" type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left text-brand-700 active:bg-gray-50" @click="create">
            <Icon name="plus" :size="16" /><span class="truncate font-medium" dir="auto">{{ createLabel }} “{{ q.trim() }}”</span>
          </button>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style>
.sheet-fade-enter-active, .sheet-fade-leave-active { transition: opacity .2s ease; }
.sheet-fade-enter-from, .sheet-fade-leave-to { opacity: 0; }
.sheet-up-enter-active, .sheet-up-leave-active { transition: transform .25s ease; }
.sheet-up-enter-from, .sheet-up-leave-to { transform: translateY(100%); }
</style>
