<script setup>
import { ref, reactive, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { localToday, ymd, price, lineTotal, itemsTotal } from "../ui"
import Icon from "../components/Icon.vue"
import PickerSheet from "../components/PickerSheet.vue"
import ConfirmSheet from "../components/ConfirmSheet.vue"

// A Sales Order for any customer. It is saved as a Draft: accounts review it and approve it.
const route = useRoute()
const router = useRouter()
const tomorrow = (() => { const d = new Date(); d.setDate(d.getDate() + 1); return ymd(d) })()
const f = reactive({
  customer: route.query.customer || "", customer_name: route.query.customer_name || route.query.customer || "",
  delivery_date: tomorrow, invoice_type: "", items: [], notes: "",
})
const pickingCustomer = ref(false)
const pickingItems = ref(false)
const error = ref("")
const saving = ref(false)
const confirming = ref(false)
const total = computed(() => itemsTotal(f.items))

async function fetchCustomers(text) {
  const rows = await call("kayanick_crm.orders_api.search_customers", { text })
  return rows.map((r) => ({ value: r.name, label: r.customer_name || r.name, sub: r.customer_name !== r.name ? r.name : "" }))
}
function pickCustomer(r) { f.customer = r.value; f.customer_name = r.label }

async function fetchItems(text) {
  const rows = await call("kayanick_crm.orders_api.search_items", { text })
  return rows.map((r) => ({ value: r.name, label: r.item_name || r.name, sub: r.name !== r.item_name ? r.name : r.stock_uom, raw: r }))
}
function pickItem(r) {
  if (f.items.some((x) => x.item_code === r.value)) return
  f.items.push({ item_code: r.value, item_name: r.raw.item_name || r.value, uom: r.raw.stock_uom, qty: 1, rate: null })
}
function unpickItem(r) { f.items = f.items.filter((x) => x.item_code !== r.value) }
function step(row, d) { row.qty = Math.max(1, (Number(row.qty) || 0) + d) }

const summary = computed(() => [
  { label: "Customer", value: f.customer_name },
  { label: "Delivery date", value: f.delivery_date },
  { label: "Invoice type", value: f.invoice_type },
  { label: "Items", value: f.items.map((r) => `${r.item_name} × ${r.qty} @ ${price(r.rate)} = ${price(lineTotal(r))}`).join("\n") },
  { label: "Total", value: price(total.value) },
  { label: "Notes", value: f.notes },
])

function fail(msg) { error.value = msg; window.scrollTo({ top: 0, behavior: "smooth" }) }
function askSave() {
  error.value = ""
  if (!f.customer) return fail("Choose the customer")
  if (!f.delivery_date || f.delivery_date < localToday()) return fail("Choose a delivery date from today on")
  if (!f.invoice_type) return fail("Choose the invoice type: System or Cash")
  if (!f.items.length) return fail("Add at least one item")
  if (f.items.some((r) => !(Number(r.qty) > 0))) return fail("Each item needs a quantity")
  if (f.items.some((r) => !(Number(r.rate) > 0))) return fail("Enter the price of each item")
  confirming.value = true
}
async function save() {
  saving.value = true
  try {
    const r = await call("kayanick_crm.orders_api.create_order", {
      payload: JSON.stringify({
        customer: f.customer, delivery_date: f.delivery_date, invoice_type: f.invoice_type, notes: f.notes,
        items: f.items.map((r) => ({ item_code: r.item_code, qty: r.qty, rate: r.rate })),
      }),
    }, { post: true })
    confirming.value = false
    router.replace({ name: "orders", query: { saved: r.name } })
  } catch (e) {
    confirming.value = false
    fail(e.message)
  } finally { saving.value = false }
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/orders")
}
</script>

<template>
  <div class="pb-24">
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1">New order</h1>
      </div>
    </header>

    <div class="wrap space-y-5 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <section>
        <p class="section-label"><Icon name="building" :size="14" />Customer</p>
        <div class="card space-y-4 p-4">
          <div>
            <label class="label">Customer<span class="text-red-500"> *</span></label>
            <button type="button" class="input flex items-center text-left" @click="pickingCustomer = true">
              <span class="min-w-0 flex-1 truncate" :class="f.customer ? '' : 'text-gray-400'" dir="auto">{{ f.customer_name || "Choose a customer" }}</span>
              <Icon name="chevron-down" :size="16" class="text-gray-400" />
            </button>
          </div>
          <div>
            <label class="label">Delivery date<span class="text-red-500"> *</span></label>
            <input v-model="f.delivery_date" type="date" class="input" :min="localToday()" />
          </div>
          <div>
            <p class="label">Invoice type<span class="text-red-500"> *</span></p>
            <div class="grid grid-cols-2 gap-2">
              <button v-for="o in ['System', 'Cash']" :key="o" type="button" class="btn h-10 border"
                :class="f.invoice_type === o ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white'" @click="f.invoice_type = o">
                <Icon v-if="f.invoice_type === o" name="check" :size="14" />{{ o }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="package" :size="14" />Items<span class="text-red-500"> *</span><span v-if="f.items.length" class="text-gray-400">· {{ f.items.length }}</span></p>
        <div class="card space-y-3 p-4">
          <div v-for="(row, i) in f.items" :key="row.item_code" class="rounded-lg border border-gray-200 px-3 py-2">
            <div class="flex items-start gap-2">
              <span class="min-w-0 flex-1">
                <span class="block break-words text-sm font-medium" dir="auto">{{ row.item_name }}</span>
                <span v-if="row.item_code !== row.item_name" class="block break-words text-xs text-gray-500">{{ row.item_code }}</span>
              </span>
              <button type="button" class="p-1 text-gray-400" aria-label="Remove" @click="f.items.splice(i, 1)"><Icon name="x" :size="14" /></button>
            </div>
            <div class="mt-2 flex items-center justify-end gap-2">
              <span v-if="row.uom" class="mr-auto text-xs text-gray-500">{{ row.uom }}</span>
              <button type="button" class="btn btn-subtle h-8 w-8 px-0" aria-label="Less" @click="step(row, -1)">−</button>
              <input v-model.number="row.qty" type="number" inputmode="decimal" min="0" step="any" class="input h-8 w-16 px-1 text-center" aria-label="Quantity" />
              <button type="button" class="btn btn-subtle h-8 w-8 px-0" aria-label="More" @click="step(row, 1)"><Icon name="plus" :size="14" /></button>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <label class="text-xs text-gray-500" :for="'order-rate-' + i">Price<span class="text-red-500"> *</span></label>
              <input :id="'order-rate-' + i" v-model.number="row.rate" type="number" inputmode="decimal" min="0" step="any" placeholder="0" class="input h-8 w-28 px-2 text-right" />
              <span class="ml-auto text-sm font-medium">{{ price(lineTotal(row)) }}</span>
            </div>
          </div>
          <button type="button" class="btn btn-subtle h-10 w-full" @click="pickingItems = true"><Icon name="plus" :size="15" />Add item</button>
          <div v-if="f.items.length" class="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm">
            <span class="text-gray-500">Total before tax</span><span class="font-semibold">{{ price(total) }}</span>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
        <div class="card p-4">
          <textarea v-model="f.notes" rows="3" placeholder="Anything accounts should know (optional)" class="input h-auto resize-none py-2" dir="auto"></textarea>
        </div>
      </section>
      <p class="text-xs text-gray-400">The order is saved as a draft. Accounts review it and approve it.</p>
    </div>

    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="wrap py-3">
        <button type="button" class="btn btn-primary h-11 w-full text-[15px]" :disabled="saving" @click="askSave">
          {{ saving ? "Saving…" : "Place order" }}
        </button>
      </div>
    </div>

    <PickerSheet v-model:open="pickingCustomer" title="Customer" placeholder="Search customers" :fetcher="fetchCustomers" @pick="pickCustomer" />
    <PickerSheet v-model:open="pickingItems" title="Items" placeholder="Search items" multi
      :fetcher="fetchItems" :selected="f.items.map((x) => x.item_code)" @pick="pickItem" @unpick="unpickItem" />
    <ConfirmSheet v-model:open="confirming" title="Place this order?" :rows="summary" confirm-text="Place order"
      :busy="saving" @confirm="save" />
  </div>
</template>
