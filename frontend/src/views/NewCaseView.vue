<script setup>
import { ref, reactive, computed, watch } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import { initials, localToday } from "../ui"
import Icon from "../components/Icon.vue"

const router = useRouter()
const f = reactive({ customer: null, case_date: localToday(), notes: "", items: [] })
const cq = ref("")
const customers = ref([])
const iq = ref("")
const itemHits = ref([])
const saving = ref(false)
const error = ref("")
let ct = null
let it = null

const totalQty = computed(() => f.items.reduce((s, i) => s + (Number(i.qty) || 0), 0))
const canSave = computed(() => f.customer && f.items.length && !saving.value)

watch(cq, (v) => {
  clearTimeout(ct)
  ct = setTimeout(async () => {
    try { customers.value = await call("kayanick_crm.case_api.search_customers", { text: v || "" }) }
    catch (e) { error.value = e.message }
  }, 250)
}, { immediate: true })
watch(iq, (v) => {
  clearTimeout(it)
  if (!v || v.length < 2) { itemHits.value = []; return }
  it = setTimeout(async () => {
    try { itemHits.value = await call("kayanick_crm.case_api.search_items", { text: v }) }
    catch (e) { error.value = e.message }
  }, 250)
})

function pickCustomer(c) { f.customer = c; cq.value = "" }
function addItem(i) {
  const row = f.items.find((r) => r.item_code === i.name)
  if (row) row.qty = Number(row.qty) + 1
  else f.items.push({ item_code: i.name, item_name: i.item_name, uom: i.stock_uom, qty: 1 })
  iq.value = ""
  itemHits.value = []
}
function step(row, d) { row.qty = Math.max(1, (Number(row.qty) || 0) + d) }
function remove(row) { f.items.splice(f.items.indexOf(row), 1) }
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/cases")
}

async function save() {
  error.value = ""
  if (!f.customer) { error.value = "Choose a customer first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  if (!f.items.length) { error.value = "Add at least one item"; return }
  saving.value = true
  try {
    const r = await call("kayanick_crm.case_api.create_case", {
      payload: JSON.stringify({
        customer: f.customer.name, case_date: f.case_date, notes: f.notes,
        items: f.items.map((i) => ({ item_code: i.item_code, qty: Number(i.qty) })),
      }),
    }, { post: true })
    router.push({ name: "cases", query: { so: r.sales_order } })
  } catch (e) {
    error.value = e.message
    window.scrollTo({ top: 0, behavior: "smooth" })
  } finally { saving.value = false }
}
</script>

<template>
  <div class="pb-24">
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1">New case</h1>
      </div>
    </header>

    <div class="wrap space-y-5 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <section>
        <p class="section-label"><Icon name="building" :size="14" />Customer</p>
        <div class="card space-y-4 p-4">
          <div v-if="f.customer" class="flex items-center gap-3 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2">
            <span class="avatar h-8 w-8 bg-white text-brand-700">{{ initials(f.customer.customer_name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ f.customer.customer_name }}</span>
              <span class="block truncate text-xs text-gray-500">{{ f.customer.name }}</span>
            </span>
            <button type="button" class="text-sm font-medium text-brand-700" @click="f.customer = null">Change</button>
          </div>
          <template v-else>
            <div class="relative">
              <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
              <input v-model="cq" type="search" placeholder="Search customers" class="input pl-9" dir="auto" />
            </div>
            <div v-if="customers.length" class="card max-h-72 divide-y divide-gray-100 overflow-y-auto">
              <button v-for="c in customers" :key="c.name" type="button" class="flex w-full items-center gap-3 px-3 py-2.5 text-left active:bg-gray-50" @click="pickCustomer(c)">
                <span class="avatar h-8 w-8">{{ initials(c.customer_name) }}</span>
                <span class="flex-1 truncate" dir="auto">{{ c.customer_name }}</span>
                <span class="text-xs text-gray-400">{{ c.territory }}</span>
              </button>
            </div>
            <p v-else class="text-sm text-gray-400">No customers found</p>
          </template>
          <div>
            <label class="label">Case date</label>
            <input v-model="f.case_date" type="date" class="input" />
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="clipboard" :size="14" />Items <span v-if="f.items.length" class="text-gray-400">· {{ f.items.length }} lines · {{ totalQty }} pcs</span></p>
        <div class="card space-y-3 p-4">
          <div class="relative">
            <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="plus" :size="16" /></span>
            <input v-model="iq" type="search" placeholder="Add item (type 2+ letters)" class="input pl-9" dir="auto" />
          </div>
          <div v-if="itemHits.length" class="card max-h-64 divide-y divide-gray-100 overflow-y-auto">
            <button v-for="i in itemHits" :key="i.name" type="button" class="flex w-full items-center gap-3 px-3 py-2.5 text-left active:bg-gray-50" @click="addItem(i)">
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium" dir="auto">{{ i.item_name }}</span>
                <span class="block truncate text-xs text-gray-400">{{ i.name }}</span>
              </span>
              <Icon name="plus" :size="16" class="text-brand-600" />
            </button>
          </div>

          <p v-if="!f.items.length" class="py-2 text-center text-sm text-gray-400">No items yet</p>
          <div v-else class="divide-y divide-gray-100 rounded-lg border border-gray-200">
            <div v-for="row in f.items" :key="row.item_code" class="flex items-center gap-3 px-3 py-2.5">
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium" dir="auto">{{ row.item_name }}</p>
                <p class="truncate text-xs text-gray-400">{{ row.item_code }} · {{ row.uom }}</p>
              </div>
              <div class="flex items-center rounded-lg border border-gray-200">
                <button type="button" class="h-8 w-8 text-lg text-gray-600" @click="step(row, -1)">−</button>
                <input v-model="row.qty" type="number" min="1" inputmode="decimal" class="h-8 w-12 border-x border-gray-200 text-center text-sm outline-none" />
                <button type="button" class="h-8 w-8 text-lg text-gray-600" @click="step(row, 1)">+</button>
              </div>
              <button type="button" class="p-1 text-gray-400" aria-label="Remove" @click="remove(row)"><Icon name="x" :size="16" /></button>
            </div>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
        <div class="card p-4">
          <textarea v-model="f.notes" rows="3" placeholder="Doctor, procedure, anything the office should know" class="input h-auto resize-none py-2" dir="auto"></textarea>
        </div>
      </section>
    </div>

    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="wrap py-3">
        <button type="button" class="btn btn-primary h-11 w-full text-[15px]" :disabled="!canSave" @click="save">
          {{ saving ? "Creating…" : "Create Sales Order" }}
        </button>
      </div>
    </div>
  </div>
</template>
