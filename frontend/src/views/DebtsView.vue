<script setup>
import { ref, computed, watch, onActivated, onMounted } from "vue"
import { call } from "../api"
import { initials, money } from "../ui"
import Icon from "../components/Icon.vue"

defineOptions({ name: "DebtsView" })
const data = ref(null)
const error = ref("")
const loading = ref(false)
const text = ref("")
const rep = ref("")
const overdueOnly = ref(false)
const team = ref([])

const rows = computed(() => {
  if (!data.value) return []
  const q = text.value.trim().toLowerCase()
  return data.value.customers.filter((c) => (!q || c.customer_name.toLowerCase().includes(q))
    && (!overdueOnly.value || c.overdue > 0))
})

async function load() {
  loading.value = true
  error.value = ""
  try { data.value = await call("kayanick_crm.debt_api.get_debts", rep.value ? { employee: rep.value } : {}) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
watch(rep, load)
// kept alive: coming back from a customer refreshes in place
onActivated(load)
onMounted(async () => {
  try { team.value = await call("kayanick_crm.mobile.get_team") } catch (e) {}
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
            <p class="text-xs text-brand-100">Customers</p>
            <p class="font-semibold">{{ data.totals.customers }}</p>
          </div>
        </div>
      </div>

      <div class="space-y-2">
        <div class="relative">
          <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
          <input v-model="text" type="search" placeholder="Customer" class="input pl-9" dir="auto" />
        </div>
        <div class="flex gap-2">
          <select v-if="team.length" v-model="rep" class="input flex-1">
            <option value="">Everyone</option>
            <option v-for="r in team" :key="r.user" :value="r.user">{{ r.name }}</option>
          </select>
          <button type="button" class="chip h-10" :class="{ 'chip-on': overdueOnly }" @click="overdueOnly = !overdueOnly">Overdue only</button>
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
            </div>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </router-link>
        </div>
        <p class="py-1 text-center text-xs text-gray-400">{{ rows.length }} customer{{ rows.length === 1 ? "" : "s" }}</p>
      </template>
    </div>
  </div>
</template>
