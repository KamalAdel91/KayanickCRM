<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const data = ref(null)
const error = ref("")
const loading = ref(true)
const busy = ref("")
const toast = ref(route.query.saved ? "Visit " + route.query.saved + " saved" : "")

const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"
})
const firstName = computed(() => ((data.value && data.value.user) || "").split(" ")[0])
const overdue = computed(() => (data.value ? data.value.tasks.filter((t) => t.is_overdue).length : 0))
const dateLabel = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })

function fmt(d) {
  if (!d) return ""
  return new Date(d + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })
}
function initials(s) {
  return (s || "?").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase()
}
const userInitials = computed(() => initials(data.value && data.value.user))

const next = computed(() => {
  if (!data.value) return null
  const t = data.value.tasks.find((x) => x.is_overdue) || data.value.tasks[0]
  if (t) {
    return {
      kind: "task", task: t, title: t.task_description,
      sub: [t.hospital_title, t.doctor_title].filter(Boolean).join(" · "),
      when: t.is_overdue ? "Overdue since " + fmt(t.due_date) : "Due " + fmt(t.due_date),
      hospital: t.hospital_account, hospitalTitle: t.hospital_title,
    }
  }
  const a = data.value.due_visits[0]
  if (a) {
    return {
      kind: "visit", title: "Visit " + a.account_name,
      sub: [a.city, a.tier ? "Tier " + a.tier : ""].filter(Boolean).join(" · "),
      when: "Planned " + fmt(a.next_visit), hospital: a.name, hospitalTitle: a.account_name,
    }
  }
  return null
})

async function load() {
  loading.value = true
  error.value = ""
  try { data.value = await call("kayanick_crm.mobile.get_today") }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
async function done(t) {
  busy.value = t.name
  try {
    await call("kayanick_crm.mobile.complete_task", { task: t.name }, { post: true })
    toast.value = "Task completed"
    setTimeout(() => (toast.value = ""), 2500)
    await load()
  } catch (e) { error.value = e.message }
  finally { busy.value = "" }
}
function logVisit(hospital, title) {
  router.push({ name: "visit", query: hospital ? { hospital, title } : {} })
}
onMounted(() => {
  load()
  if (toast.value) {
    router.replace({ query: {} })
    setTimeout(() => (toast.value = ""), 3000)
  }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">K</span>
        <div class="flex-1 leading-tight">
          <p class="text-[11px] font-medium uppercase tracking-wide text-gray-400">Kayanick CRM</p>
          <h1 class="text-base font-semibold">Today</h1>
        </div>
        <button class="btn btn-subtle w-9 px-0" aria-label="Refresh" @click="load"><Icon name="refresh" :size="16" /></button>
        <span class="avatar bg-brand-50 text-brand-700">{{ userInitials }}</span>
      </div>
    </header>

    <div class="wrap space-y-5 py-4">
      <div>
        <p class="text-lg font-semibold">{{ greeting }}<span v-if="firstName">, {{ firstName }}</span></p>
        <p class="text-sm text-gray-500">{{ dateLabel }}</p>
      </div>

      <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <div v-if="next" class="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white shadow-md shadow-brand-600/20">
        <p class="text-[11px] font-semibold uppercase tracking-wider text-brand-100">Next up</p>
        <p class="mt-1 text-lg font-semibold leading-snug" dir="auto">{{ next.title }}</p>
        <p v-if="next.sub" class="text-sm text-brand-100" dir="auto">{{ next.sub }}</p>
        <p class="mt-1.5 flex items-center gap-1 text-xs" :class="next.task && next.task.is_overdue ? 'text-red-200' : 'text-brand-100'">
          <Icon name="calendar" :size="12" />{{ next.when }}
        </p>
        <div class="mt-3 flex gap-2">
          <button v-if="next.kind === 'task'" class="btn bg-white/15 text-white" :disabled="busy === next.task.name" @click="done(next.task)">
            <Icon name="check" :size="15" />Done
          </button>
          <button v-if="next.hospital" class="btn bg-white text-brand-700" @click="logVisit(next.hospital, next.hospitalTitle)">
            <Icon name="plus" :size="15" />Log visit
          </button>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-2">
        <div class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><Icon name="clipboard" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold">{{ data ? data.tasks.length : "–" }}</p>
          <p class="text-xs text-gray-500">Open tasks</p>
        </div>
        <div class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-red-600"><Icon name="alert" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold" :class="overdue ? 'text-red-600' : ''">{{ data ? overdue : "–" }}</p>
          <p class="text-xs text-gray-500">Overdue</p>
        </div>
        <div class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-green-50 text-green-600"><Icon name="calendar" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold">{{ data ? data.due_visits.length : "–" }}</p>
          <p class="text-xs text-gray-500">Visits due</p>
        </div>
      </div>

      <template v-if="loading && !data">
        <div v-for="i in 3" :key="i" class="card h-20 animate-pulse"></div>
      </template>

      <template v-else-if="data">
        <section>
          <p class="section-label">Tasks</p>
          <div v-if="!data.tasks.length" class="empty"><Icon name="check" :size="24" /><p>You're all caught up</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <div v-for="t in data.tasks" :key="t.name" class="flex gap-3 px-4 py-3">
              <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="t.is_overdue ? 'bg-red-500' : 'bg-brand-500'"></span>
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-3">
                  <p class="font-medium leading-snug" dir="auto">{{ t.task_description }}</p>
                  <span class="badge" :class="t.is_overdue ? 'badge-red' : 'badge-gray'">{{ t.is_overdue ? "Overdue" : fmt(t.due_date) }}</span>
                </div>
                <p v-if="t.hospital_title" class="mt-0.5 text-sm text-gray-500" dir="auto">{{ [t.hospital_title, t.doctor_title].filter(Boolean).join(" · ") }}</p>
                <p class="text-xs text-gray-400">{{ t.task_type || "Task" }} · due {{ fmt(t.due_date) }}</p>
                <div class="mt-2.5 flex gap-2">
                  <button class="btn btn-subtle" :disabled="busy === t.name" @click="done(t)">
                    <Icon name="check" :size="15" />{{ busy === t.name ? "Saving…" : "Done" }}
                  </button>
                  <button v-if="t.hospital_account" class="btn btn-primary" @click="logVisit(t.hospital_account, t.hospital_title)">
                    <Icon name="plus" :size="15" />Log visit
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="pb-2">
          <p class="section-label">Due for a visit</p>
          <div v-if="!data.due_visits.length" class="empty"><Icon name="calendar" :size="24" /><p>No visits due</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <div v-for="a in data.due_visits" :key="a.name" class="flex items-center gap-3 px-4 py-3">
              <span class="avatar">{{ initials(a.account_name) }}</span>
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium" dir="auto">{{ a.account_name }}</p>
                <p class="truncate text-xs" :class="a.is_overdue ? 'text-red-600' : 'text-gray-500'">
                  {{ [a.city, a.tier ? "Tier " + a.tier : ""].filter(Boolean).join(" · ") }} · planned {{ fmt(a.next_visit) }}
                </p>
              </div>
              <button class="btn btn-subtle" @click="logVisit(a.name, a.account_name)">Visit</button>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>
