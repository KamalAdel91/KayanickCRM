<script setup>
import { ref, reactive, computed } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import { localToday } from "../ui"
import Icon from "../components/Icon.vue"
import AttachPicker from "../components/AttachPicker.vue"
import PickerSheet from "../components/PickerSheet.vue"
import PickField from "../components/PickField.vue"
import ConfirmSheet from "../components/ConfirmSheet.vue"
import { uploadFiles } from "../upload"

const router = useRouter()
const f = reactive({ customer: null, case_date: localToday(), notes: "", items: [] })
const sheet = ref("")
const saving = ref(false)
const attachments = ref([])
const confirming = ref(false)
const error = ref("")

const totalQty = computed(() => f.items.reduce((s, i) => s + (Number(i.qty) || 0), 0))
const canSave = computed(() => f.customer && f.items.length && !saving.value)
const selectedCodes = computed(() => f.items.map((i) => i.item_code))
const customerOpen = computed({ get: () => sheet.value === "customer", set: (v) => (sheet.value = v ? "customer" : "") })
const itemOpen = computed({ get: () => sheet.value === "item", set: (v) => (sheet.value = v ? "item" : "") })

async function fetchCustomers(text) {
  const r = await call("kayanick_crm.case_api.search_customers", { text })
  return r.map((c) => ({ value: c.name, label: c.customer_name, sub: [c.name !== c.customer_name ? c.name : "", c.territory].filter(Boolean).join(" · "), raw: c }))
}
async function fetchItems(text) {
  const r = await call("kayanick_crm.case_api.search_items", { text })
  return r.map((i) => ({ value: i.name, label: i.item_name, sub: [i.name !== i.item_name ? i.name : "", i.stock_uom].filter(Boolean).join(" · "), raw: i }))
}
function addItem(r) {
  const i = r.raw
  const row = f.items.find((x) => x.item_code === i.name)
  if (row) row.qty = Number(row.qty) + 1
  else f.items.push({ item_code: i.name, item_name: i.item_name, uom: i.stock_uom, qty: 1 })
}
function removeItem(r) {
  const row = f.items.find((x) => x.item_code === r.value)
  if (row) remove(row)
}
function step(row, d) { row.qty = Math.max(1, (Number(row.qty) || 0) + d) }
function remove(row) { f.items.splice(f.items.indexOf(row), 1) }
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/cases")
}

const summary = computed(() => [
  { label: "Customer", value: f.customer ? f.customer.customer_name : "" },
  { label: "Case date", value: f.case_date },
  { label: "Items", value: f.items.map((i) => i.qty + " × " + i.item_name).join("\n") },
  { label: "Notes", value: f.notes },
  { label: "Attachments", value: attachments.value.length ? String(attachments.value.length) : "" },
])

function askSave() {
  error.value = ""
  if (!f.customer) { error.value = "Choose a customer first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  if (!f.items.length) { error.value = "Add at least one item"; return }
  confirming.value = true
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
      make_order: 0,
    }, { post: true })
    // files go on the case before the order, because the case is locked once the order exists
    const failed = attachments.value.length ? await uploadFiles("KC Case", r.case, attachments.value) : []
    if (failed.length) alert("These files failed to upload:\n" + failed.join("\n"))
    confirming.value = false
    try {
      const so = await call("kayanick_crm.case_api.make_sales_order", { case: r.case }, { post: true })
      router.push({ name: "cases", query: { so } })
    } catch (e) {
      router.push({ name: "case-detail", params: { name: r.case }, query: { error: e.message } })
    }
  } catch (e) {
    confirming.value = false
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
          <PickField :value="f.customer ? f.customer.customer_name : ''" :sub="f.customer ? f.customer.name : ''" icon="building"
            placeholder="Choose customer" @open="sheet = 'customer'" @clear="f.customer = null" />
          <div>
            <label class="label">Case date</label>
            <input v-model="f.case_date" type="date" class="input" />
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="clipboard" :size="14" />Items <span v-if="f.items.length" class="text-gray-400">· {{ f.items.length }} lines · {{ totalQty }} pcs</span></p>
        <div class="card space-y-3 p-4">
          <button type="button" class="btn btn-subtle w-full" @click="sheet = 'item'"><Icon name="plus" :size="16" />Add items</button>
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

      <section>
        <p class="section-label"><Icon name="paperclip" :size="14" />Attachments<span v-if="attachments.length" class="text-gray-400">· {{ attachments.length }}</span></p>
        <div class="card p-4"><AttachPicker v-model="attachments" /></div>
      </section>
    </div>

    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="wrap py-3">
        <button type="button" class="btn btn-primary h-11 w-full text-[15px]" :disabled="!canSave" @click="askSave">
          {{ saving ? (attachments.length ? "Creating & uploading…" : "Creating…") : "Create Sales Order" }}
        </button>
      </div>
    </div>

    <ConfirmSheet v-model:open="confirming" title="Create this Sales Order?" :rows="summary" confirm-text="Create order"
      note="The case is locked once the Sales Order is created." :busy="saving" @confirm="save" />
    <PickerSheet v-model:open="customerOpen" title="Choose customer" placeholder="Search customers"
      :fetcher="fetchCustomers" @pick="(r) => (f.customer = r.raw)" />
    <PickerSheet v-model:open="itemOpen" title="Add items" placeholder="Search items" multi :selected="selectedCodes"
      :fetcher="fetchItems" @pick="addItem" @unpick="removeItem" />
  </div>
</template>
