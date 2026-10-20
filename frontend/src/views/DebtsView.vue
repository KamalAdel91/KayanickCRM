<script setup>
import { ref, computed, watch, onActivated } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials, money } from "../ui"
import Icon from "../components/Icon.vue"

defineOptions({ name: "DebtsView" })
const route = useRoute()
const router = useRouter()
const data = ref(null)
const error = ref("")
const loading = ref(false)
const text = ref("")
const rep = ref("")
const overdueOnly = ref(false)
const sortBy = ref("amount")  // amount | late
const team = computed(() => (data.value && data.value.reps) || [])

const rows = computed(() => {
  if (!data.value) return []
  const q = text.value.trim().toLowerCase()
  const out = data.value.customers.filter((c) => (!q || c.customer_name.toLowerCase().includes(q))
    && (!overdueOnly.value || c.overdue > 0))
  if (sortBy.value === "late") out.sort((a, b) => b.max_days - a.max_days || b.overdue - a.overdue)
  return out
})
// aging bar: share of the overdue amount per bucket
const AGING_COLOR = { "1-30": "bg-amber-300", "31-60": "bg-amber-500", "61-90": "bg-red-400", "90+": "bg-red-600" }
const aging = computed(() => {
  if (!data.value || !data.value.totals.overdue) return []
  return data.value.aging.filter((a) => a.amount > 0)
    .map((a) => ({ ...a, pct: (a.amount / data.value.totals.overdue) * 100, color: AGING_COLOR[a.label] }))
})

async function load() {
  loading.value = true
  error.value = ""
  try { data.value = await call("kayanick_crm.debt_api.get_debts", rep.value ? { employee: rep.value } : {}) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
watch(rep, load)
// kept alive: coming back from a customer refreshes in place. ?overdue=1 comes from the Today card
onActivated(() => {
  if (route.query.overdue) {
    overdueOnly.value = true
    sortBy.value = "late"
    router.replace({ query: {} })
  }
  load()
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Customer debt</h1>
        <button class="btn btn-subtle w-9 px-0" aria-label="Refresh" @click="load"><Icon name="refresh" :size="16" /></button>
      </div>
    </header>
    <div class="wrap space-y-3 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <div v-if="data" class="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white shadow-md shadow-brand-600/20">
        <p class="text-[11px] font-semibold uppercase tracking-wider text-brand-100">Total owed</p>
        <p class="mt-1 text-2xl font-semibold">{{ money(data.totals.balance) }} <span class="text-sm font-medium text-brand-100">{{ data.currency }}</span></p>
        <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div class="rounded-lg bg-white/10 px-3 py-2">
            <p class="text-xs text-brand-100">Overdue</p>
            <p class="font-semibold">{{ money(data.totals.overdue) }}</p>
          </div>
          <div class="rounded-lg bg-white/10 px-3 py-2">
            <p class="text-xs text-brand-100">Due in 7 days</p>
            <p class="font-semibold">{{ money(data.totals.due_soon) }}</p>
          </div>
        </div>
      </div>

      <div v-if="aging.length" class="card p-3">
        <p class="mb-2 text-xs font-medium text-gray-500">Overdue by age (days late)</p>
        <div class="flex h-2.5 overflow-hidden rounded-full bg-gray-100">
          <div v-for="a in aging" :key="a.label" :class="a.color" :style="{ width: a.pct + '%' }"></div>
        </div>
        <div class="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
          <div v-for="a in aging" :key="a.label" class="flex items-center gap-1.5">
            <span class="h-2 w-2 rounded-full" :class="a.color"></span>
            <span class="text-gray-500">{{ a.label }}</span>
            <span class="ml-auto font-medium">{{ money(a.amount) }}</span>
          </div>
        </div>
      </div>

      <div class="space-y-2">
        <div class="relative">
          <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
          <input v-model="text" type="search" placeholder="Customer" class="input pl-9" dir="auto" />
        </div>
        <div class="flex gap-2">
          <select v-if="team.length" v-model="rep" class="input min-w-0 flex-1">
            <option value="">Everyone</option>
            <option v-for="r in team" :key="r.employee" :value="r.employee">{{ r.name }}</option>
          </select>
          <button type="button" class="chip h-10" :class="{ 'chip-on': overdueOnly }" @click="overdueOnly = !overdueOnly">Overdue</button>
          <button type="button" class="chip h-10" :class="{ 'chip-on': sortBy === 'late' }" @click="sortBy = sortBy === 'late' ? 'amount' : 'late'">Most late</button>
        </div>
      </div>

      <template v-if="loading && !data">
        <div v-for="i in 4" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="data && !rows.length" class="empty">
        <Icon name="wallet" :size="24" /><p>No customer debt</p>
      </div>
      <template v-else-if="data">
        <div class="card divide-y divide-gray-100">
          <router-link v-for="c in rows" :key="c.customer" :to="{ name: 'debt', params: { customer: c.customer } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
            <span class="avatar">{{ initials(c.customer_name) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate font-medium" dir="auto">{{ c.customer_name }}</p>
              <p class="truncate text-xs text-gray-500" dir="auto">{{ [c.invoices + (c.invoices === 1 ? " invoice" : " invoices"), team.length ? c.rep_name || "No rep" : ""].filter(Boolean).join(" · ") }}</p>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span class="text-sm font-semibold" :class="c.balance < 0 ? 'text-green-700' : ''">{{ money(c.balance) }}</span>
              <span v-if="c.max_days" class="badge" :class="c.max_days > 90 ? 'badge-red' : 'badge-amber'">{{ c.max_days }}d overdue</span>
              <span v-else-if="c.next_due" class="badge badge-blue">Due {{ fmt(c.next_due) }}</span>
            </div>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </router-link>
        </div>
        <p class="py-1 text-center text-xs text-gray-400">{{ rows.length }} customer{{ rows.length === 1 ? "" : "s" }}</p>
      </template>
    </div>
  </div>
</template>
