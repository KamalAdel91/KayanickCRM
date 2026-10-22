<script setup>
import { ref, reactive, watch, onActivated } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials, money } from "../ui"
import { usePaged } from "../paged"
import { getOptions } from "../options"
import Icon from "../components/Icon.vue"

defineOptions({ name: "OrdersView" })

const route = useRoute()
const router = useRouter()
const f = reactive({ status: "", employee: "" })
const tabs = [{ label: "All", value: "" }, { label: "Waiting", value: "draft" }, { label: "Approved", value: "approved" }, { label: "Cancelled", value: "cancelled" }]
const paged = usePaged("kayanick_crm.orders_api.get_orders", () => ({ ...f }))
const { rows, loading, done, error, reload, more } = paged
watch(f, reload)
const team = ref([])
const canOrder = ref(false)
const toast = ref("")
let first = true

const badge = (o) => (o.docstatus === 0 ? "badge-amber" : o.docstatus === 2 ? "badge-red" : "badge-green")

onActivated(() => {
  if (route.query.saved) {
    toast.value = "Order " + route.query.saved + " sent for review"
    setTimeout(() => (toast.value = ""), 3500)
    router.replace({ query: {} })
  }
  if (first) {
    first = false
    reload()
    getOptions().then((o) => (canOrder.value = !!o.can_order)).catch(() => {})
    call("kayanick_crm.mobile.get_team").then((t) => (team.value = t)).catch(() => {})
  } else paged.refresh()
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Orders</h1>
        <router-link v-if="canOrder" to="/orders/new" class="btn btn-primary"><Icon name="plus" :size="15" />New order</router-link>
      </div>
    </header>

    <div class="wrap space-y-3 py-4">
      <div class="grid grid-cols-4 rounded-lg bg-gray-100 p-1 text-sm font-medium">
        <button v-for="t in tabs" :key="t.label" type="button" class="rounded-md py-1.5"
          :class="f.status === t.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="f.status = t.value">{{ t.label }}</button>
      </div>
      <select v-if="team.length" v-model="f.employee" class="input" aria-label="Rep">
        <option value="">All reps</option>
        <option v-for="r in team" :key="r.user" :value="r.user">{{ r.name }}</option>
      </select>
      <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <template v-if="loading && !rows.length">
        <div v-for="i in 3" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty">
        <Icon name="package" :size="24" /><p>No orders yet</p>
      </div>
      <template v-else>
        <div class="card divide-y divide-gray-100">
          <router-link v-for="o in rows" :key="o.name" :to="{ name: 'order', params: { name: o.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
            <span class="avatar">{{ initials(o.customer_name) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate font-medium" dir="auto">{{ o.customer_name }}</p>
              <p class="truncate text-xs text-gray-500">{{ [fmt(o.transaction_date), o.rep_name, money(o.grand_total) + " " + o.currency].filter(Boolean).join(" · ") }}</p>
            </div>
            <span class="badge" :class="badge(o)">{{ o.state }}</span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </router-link>
        </div>
        <button v-if="!done" type="button" class="btn btn-subtle w-full" :disabled="loading" @click="more">{{ loading ? "Loading…" : "Load more" }}</button>
        <p v-else class="py-1 text-center text-xs text-gray-400">{{ rows.length }} order{{ rows.length === 1 ? "" : "s" }}</p>
      </template>
    </div>
  </div>
</template>
