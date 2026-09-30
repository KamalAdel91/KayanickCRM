<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import { pushAvailable, pushOn, enablePush, disablePush } from "../push"
import Icon from "../components/Icon.vue"

const router = useRouter()
const rows = ref([])
const loading = ref(true)
const error = ref("")
const canPush = pushAvailable()
const push = ref(pushOn())
const pushBusy = ref(false)
const testMsg = ref("")
async function testPush() {
  testMsg.value = "Sending…"
  try {
    const r = await call("kayanick_crm.notify.test_push", {}, { post: true })
    testMsg.value = r && r.success ? "Sent — it should arrive in a few seconds" : "Relay said: " + ((r && r.message) || JSON.stringify(r))
  } catch (e) { testMsg.value = e.message }
}

function ago(ts) {
  const s = Math.max(1, Math.round((Date.now() - new Date(String(ts).replace(" ", "T")).getTime()) / 1000))
  if (s < 3600) return Math.max(1, Math.round(s / 60)) + "m"
  if (s < 86400) return Math.round(s / 3600) + "h"
  return Math.round(s / 86400) + "d"
}
async function load() {
  loading.value = true
  try { rows.value = await call("kayanick_crm.notify.get_notifications") }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
async function open(n) {
  if (!n.read) {
    n.read = 1
    call("kayanick_crm.notify.mark_read", { name: n.name }, { post: true }).catch(() => {})
  }
  if (n.route) router.push(n.route)
}
async function readAll() {
  await call("kayanick_crm.notify.mark_read", {}, { post: true })
  rows.value.forEach((n) => (n.read = 1))
}
async function togglePush() {
  pushBusy.value = true
  error.value = ""
  try {
    if (push.value) await disablePush()
    else await enablePush()
    push.value = pushOn()
  } catch (e) { error.value = e.message }
  finally { pushBusy.value = false }
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/")
}
onMounted(load)
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1">Notifications</h1>
        <button v-if="rows.some((n) => !n.read)" type="button" class="btn btn-subtle" @click="readAll">Mark all read</button>
      </div>
    </header>

    <div class="wrap space-y-3 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <button v-if="canPush" type="button" class="card flex w-full items-center gap-3 p-3 text-left" :disabled="pushBusy" @click="togglePush">
        <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><Icon name="bell" :size="18" /></span>
        <span class="min-w-0 flex-1">
          <span class="block text-sm font-medium">Phone notifications</span>
          <span class="block text-xs text-gray-500">{{ pushBusy ? "Please wait…" : push ? "On — you'll get alerts even when the app is closed" : "Off — tap to turn on" }}</span>
        </span>
        <span class="relative h-6 w-11 shrink-0 rounded-full transition" :class="push ? 'bg-brand-600' : 'bg-gray-200'">
          <span class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all" :class="push ? 'left-[22px]' : 'left-0.5'"></span>
        </span>
      </button>
      <div v-if="canPush && push" class="flex items-center gap-2">
        <button type="button" class="btn btn-subtle" @click="testPush"><Icon name="bell" :size="14" />Send test</button>
        <span class="min-w-0 flex-1 text-xs text-gray-500">{{ testMsg }}</span>
      </div>

      <template v-if="loading">
        <div v-for="i in 4" :key="i" class="card h-14 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty"><Icon name="bell" :size="24" /><p>No notifications yet</p></div>
      <div v-else class="card divide-y divide-gray-100">
        <button v-for="n in rows" :key="n.name" type="button" class="flex w-full items-start gap-3 px-4 py-3 text-left active:bg-gray-50" @click="open(n)">
          <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="n.read ? 'bg-transparent' : 'bg-brand-600'"></span>
          <span class="min-w-0 flex-1 text-sm" :class="n.read ? 'text-gray-600' : 'font-medium text-gray-900'" dir="auto">{{ n.subject }}</span>
          <span class="shrink-0 text-xs text-gray-400">{{ ago(n.creation) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
