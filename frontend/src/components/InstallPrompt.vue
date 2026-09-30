<script setup>
import { ref, computed, onMounted } from "vue"
import { installEvent, isStandalone, isIOS } from "../install"
import Icon from "./Icon.vue"

const KEY = "kc_install_dismissed"
const WAIT_DAYS = 7
const snoozed = ref(false)
const ios = isIOS()

onMounted(() => {
  try {
    const t = Number(localStorage.getItem(KEY) || 0)
    snoozed.value = Date.now() - t < WAIT_DAYS * 864e5
  } catch (e) { snoozed.value = false }
})
const show = computed(() => !snoozed.value && !isStandalone() && (installEvent.value || ios))

function later() {
  snoozed.value = true
  try { localStorage.setItem(KEY, String(Date.now())) } catch (e) {}
}
async function install() {
  const e = installEvent.value
  if (!e) return
  e.prompt()
  const choice = await e.userChoice
  installEvent.value = null
  if (choice.outcome !== "accepted") later()
}
</script>

<template>
  <transition name="sheet-up">
    <div v-if="show" class="fixed inset-x-0 bottom-20 z-30 mx-auto max-w-lg px-3">
      <div class="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-3 shadow-xl">
        <img src="/icon-192.png" class="h-11 w-11 shrink-0 rounded-xl" alt="" />
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold">Install Kayanick CRM</p>
          <p v-if="installEvent" class="text-xs text-gray-500">Add it to your home screen and open it like an app.</p>
          <p v-else class="text-xs text-gray-500">Tap <b>Share</b> <span class="inline-block rotate-180">⎋</span> then <b>Add to Home Screen</b>.</p>
          <div class="mt-2 flex gap-2">
            <button v-if="installEvent" type="button" class="btn btn-primary h-8" @click="install">Install</button>
            <button type="button" class="btn btn-subtle h-8" @click="later">{{ installEvent ? "Not now" : "Got it" }}</button>
          </div>
        </div>
        <button type="button" class="p-1 text-gray-400" aria-label="Close" @click="later"><Icon name="x" :size="16" /></button>
      </div>
    </div>
  </transition>
</template>
