<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials, outcomeBadge, fmtTime } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const data = ref(null)
const error = ref("")
const loading = ref(true)
const toast = ref(route.query.saved ? "Visit " + route.query.saved + " saved" : "")

const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"
})
const firstName = computed(() => ((data.value && data.value.user) || "").split(" ")[0])
const userInitials = computed(() => initials(data.value && data.value.user))
const dateLabel = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })
const next = computed(() => (data.value && data.value.due.length ? data.value.due[0] : null))

function when(v) {
  if (v.is_overdue) return "Overdue since " + fmt(v.next_visit_date)
  if (v.is_today) return "Due today"
  return "Planned " + fmt(v.next_visit_date)
}
async function load() {
  loading.value = true
  error.value = ""
  try { data.value = await call("kayanick_crm.mobile.get_today") }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
function caseWhen(c) {
  const at = c.case_time ? " · " + fmtTime(c.case_time) : ""
  if (c.is_overdue) return "Overdue"
  if (c.is_today) return "Today" + at
  return fmt(c.case_date) + at
}
function logVisit(v) {
  const query = {}
  if (v && v.hospital) query.hospital = v.hospital
  if (v && v.doctors && v.doctors.length) query.doctors = v.doctors.join(",")
  router.push({ name: "visit", query })
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
        <img :src="'/kayanick-icon-192.png'" class="h-8 w-8 rounded-lg border border-gray-200 object-contain" alt="Kayanick" />
        <div class="flex-1 leading-tight">
          <p class="text-[11px] font-medium uppercase tracking-wide text-gray-400">Kayanick CRM</p>
          <h1 class="text-base font-semibold">Today</h1>
        </div>
        <button class="btn btn-subtle w-9 px-0" aria-label="Refresh" @click="load"><Icon name="refresh" :size="16" /></button>
        <router-link to="/notifications" class="btn btn-subtle relative w-9 px-0" aria-label="Notifications">
          <Icon name="bell" :size="16" />
          <span v-if="data && data.unread" class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">{{ data.unread > 9 ? "9+" : data.unread }}</span>
        </router-link>
        <router-link to="/account" class="avatar bg-brand-50 text-brand-700" aria-label="Account">{{ userInitials }}</router-link>
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
        <p class="mt-1 text-lg font-semibold leading-snug" dir="auto">{{ next.hospital }}</p>
        <p v-if="next.doctor_title" class="text-sm text-brand-100" dir="auto">{{ next.doctor_title }}</p>
        <p v-if="next.next_action" class="mt-2 rounded-lg bg-white/10 px-3 py-2 text-sm" dir="auto">{{ next.next_action }}</p>
        <p class="mt-2 flex items-center gap-1 text-xs" :class="next.is_overdue ? 'text-red-200' : 'text-brand-100'">
          <Icon name="calendar" :size="12" />{{ when(next) }}
        </p>
        <button class="btn mt-3 bg-white text-brand-700" @click="logVisit(next)"><Icon name="plus" :size="15" />Log visit</button>
      </div>

      <div class="grid grid-cols-3 gap-2">
        <router-link :to="{ name: 'visits', query: { period: 'month' } }" class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><Icon name="clipboard" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold">{{ data ? data.stats.month_visits : "–" }}</p>
          <p class="text-xs text-gray-500">Visits this month</p>
        </router-link>
        <router-link :to="{ name: 'visits', query: { period: 'month', order: 1 } }" class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-green-50 text-green-600"><Icon name="cart" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold">{{ data ? data.stats.month_orders : "–" }}</p>
          <p class="text-xs text-gray-500">Orders expected</p>
        </router-link>
        <router-link :to="{ name: 'visits', query: { due: 1 } }" class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-red-600"><Icon name="calendar" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold" :class="data && data.stats.due ? 'text-red-600' : ''">{{ data ? data.stats.due : "–" }}</p>
          <p class="text-xs text-gray-500">Follow-ups due</p>
        </router-link>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <router-link :to="{ name: 'cases', query: { tab: 'all', period: 'month' } }" class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-50 text-violet-600"><Icon name="cart" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold">{{ data ? data.stats.month_cases : "–" }}</p>
          <p class="text-xs text-gray-500">Cases this month</p>
        </router-link>
        <router-link :to="{ name: 'cases', query: { tab: 'planned', due: 1 } }" class="card p-3">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-600"><Icon name="calendar" :size="15" /></span>
          <p class="mt-2 text-xl font-semibold" :class="data && data.stats.cases_due ? 'text-red-600' : ''">{{ data ? data.stats.cases_due : "–" }}</p>
          <p class="text-xs text-gray-500">Cases due</p>
        </router-link>
      </div>

      <template v-if="loading && !data">
        <div v-for="i in 3" :key="i" class="card h-20 animate-pulse"></div>
      </template>

      <template v-else-if="data">
        <section>
          <p class="section-label"><Icon name="calendar" :size="14" />Follow-ups (next 7 days)</p>
          <div v-if="!data.due.length" class="empty"><Icon name="check" :size="24" /><p>No follow-ups planned</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <button v-for="v in data.due" :key="v.name" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-gray-50" @click="logVisit(v)">
              <span class="h-2 w-2 shrink-0 rounded-full" :class="v.is_overdue ? 'bg-red-500' : v.is_today ? 'bg-amber-500' : 'bg-brand-500'"></span>
              <span class="min-w-0 flex-1">
                <span class="block truncate font-medium" dir="auto">{{ v.hospital }}</span>
                <span class="block truncate text-xs text-gray-500" dir="auto">{{ [v.doctor_title, v.next_action, v.mine ? "" : v.rep_name].filter(Boolean).join(" · ") }}</span>
              </span>
              <span class="badge" :class="v.is_overdue ? 'badge-red' : v.is_today ? 'badge-amber' : 'badge-gray'">
                {{ v.is_overdue ? "Overdue" : v.is_today ? "Today" : fmt(v.next_visit_date) }}
              </span>
            </button>
          </div>
        </section>

        <section>
          <p class="section-label"><Icon name="cart" :size="14" /><span class="flex-1">Planned cases (next 7 days)</span><router-link to="/cases" class="text-brand-700">See all</router-link></p>
          <div v-if="!data.cases.length" class="empty"><Icon name="check" :size="24" /><p>No planned cases</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <router-link v-for="c in data.cases" :key="c.name" :to="{ name: 'case-detail', params: { name: c.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
              <span class="h-2 w-2 shrink-0 rounded-full" :class="c.is_overdue ? 'bg-red-500' : c.is_today ? 'bg-amber-500' : 'bg-brand-500'"></span>
              <span class="min-w-0 flex-1">
                <span class="block truncate font-medium" dir="auto">{{ c.hospital }}</span>
                <span class="block truncate text-xs text-gray-500" dir="auto">{{ [c.doctor_title, c.products.join(", "), c.rep_name].filter(Boolean).join(" · ") }}</span>
              </span>
              <span class="badge" :class="c.is_overdue ? 'badge-red' : c.is_today ? 'badge-amber' : 'badge-gray'">{{ caseWhen(c) }}</span>
            </router-link>
          </div>
        </section>

        <section class="pb-2">
          <p class="section-label"><Icon name="clipboard" :size="14" /><span class="flex-1">Recent visits</span><router-link v-if="data.recent.length" to="/visits" class="text-brand-700">See all</router-link></p>
          <div v-if="!data.recent.length" class="empty"><Icon name="clipboard" :size="24" /><p>No visits yet</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <router-link v-for="v in data.recent" :key="v.name" :to="{ name: 'visit-detail', params: { name: v.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
              <span class="avatar">{{ initials(v.hospital) }}</span>
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium" dir="auto">{{ v.hospital }}</p>
                <p class="truncate text-xs text-gray-500" dir="auto">{{ [fmt(v.visit_date), v.doctor_title, v.visit_purpose].filter(Boolean).join(" · ") }}</p>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span v-if="v.visit_outcome" class="badge" :class="outcomeBadge(v.visit_outcome)">{{ v.visit_outcome }}</span>
                <span v-if="v.order_expected" class="badge badge-blue"><Icon name="cart" :size="11" />Order</span>
              </div>
            </router-link>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>
