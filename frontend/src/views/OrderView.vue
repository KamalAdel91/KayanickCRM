<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, price } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const o = ref(null)
const error = ref("")
const badge = (x) => (x.docstatus === 0 ? "badge-amber" : x.docstatus === 2 ? "badge-red" : "badge-green")

onMounted(async () => {
  try { o.value = await call("kayanick_crm.orders_api.get_order", { name: route.params.name }) }
  catch (e) { error.value = e.message }
})
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/orders")
}
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1 truncate">{{ route.params.name }}</h1>
      </div>
    </header>

    <div class="wrap space-y-5 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <div v-if="!o && !error" class="card h-40 animate-pulse"></div>

      <template v-if="o">
        <div class="card divide-y divide-gray-100">
          <div class="px-4 py-3">
            <p class="font-medium" dir="auto">{{ o.customer_name }}</p>
            <p class="mt-0.5 flex items-center gap-1 text-xs text-gray-500"><Icon name="user" :size="12" />{{ o.rep_name }}</p>
          </div>
          <div class="flex items-center px-4 py-3">
            <div class="flex-1">
              <p class="text-xs text-gray-500">Ordered · Delivery</p>
              <p>{{ fmt(o.transaction_date) }} · {{ fmt(o.delivery_date) }}</p>
            </div>
            <span class="badge" :class="badge(o)">{{ o.state }}</span>
          </div>
        </div>

        <section>
          <p class="section-label"><Icon name="package" :size="14" />Items · {{ o.items.length }}</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="(r, i) in o.items" :key="i" class="flex items-center gap-3 px-4 py-2.5">
              <span class="min-w-0 flex-1">
                <span class="block break-words text-sm font-medium" dir="auto">{{ r.item_name }}</span>
                <span class="block text-xs text-gray-500">{{ r.qty }}<span v-if="r.uom"> {{ r.uom }}</span> @ {{ price(r.rate) }}</span>
              </span>
              <span class="shrink-0 text-sm font-medium">{{ price(r.amount) }}</span>
            </div>
            <div class="space-y-1 px-4 py-2.5 text-sm">
              <p class="flex justify-between"><span class="text-gray-500">Total</span><span>{{ price(o.total) }}</span></p>
              <p v-if="o.taxes" class="flex justify-between"><span class="text-gray-500">Taxes</span><span>{{ price(o.taxes) }}</span></p>
              <p class="flex justify-between font-semibold"><span>Grand total</span><span>{{ price(o.grand_total) }} {{ o.currency }}</span></p>
            </div>
          </div>
        </section>

        <section v-if="o.notes.length">
          <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
          <div class="card divide-y divide-gray-100">
            <p v-for="(n, i) in o.notes" :key="i" class="whitespace-pre-line px-4 py-3 text-sm" dir="auto">{{ n.text }}</p>
          </div>
        </section>
        <p v-if="o.docstatus === 0" class="text-xs text-gray-400">Waiting for accounts to review and approve it.</p>
      </template>
    </div>
  </div>
</template>
