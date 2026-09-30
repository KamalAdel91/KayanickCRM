<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue"
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
const f = reactive({ customer: null, case_date: localToday(), attended: true, notes: "", products: [] })
const productOptions = ref([])
watch(() => f.case_date, (d) => { f.attended = !!d && d <= localToday() })
const sheet = ref("")
const saving = ref(false)
const attachments = ref([])
const confirming = ref(false)
const error = ref("")

const canSave = computed(() => f.customer && !saving.value)
const customerOpen = computed({ get: () => sheet.value === "customer", set: (v) => (sheet.value = v ? "customer" : "") })

async function fetchCustomers(text) {
  const r = await call("kayanick_crm.case_api.search_customers", { text })
  return r.map((c) => ({ value: c.name, label: c.customer_name, sub: [c.name !== c.customer_name ? c.name : "", c.territory].filter(Boolean).join(" · "), raw: c }))
}
function toggleProduct(p) {
  const i = f.products.indexOf(p)
  if (i >= 0) f.products.splice(i, 1)
  else f.products.push(p)
}
onMounted(async () => {
  try { productOptions.value = (await call("kayanick_crm.mobile.get_options")).products }
  catch (e) { error.value = e.message }
})
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/cases")
}

const summary = computed(() => [
  { label: "Customer", value: f.customer ? f.customer.customer_name : "" },
  { label: "Case date", value: f.case_date },
  { label: "Status", value: f.attended ? "Attended" : "Planned (follow-up)" },
  { label: "Products", value: f.products.join(", ") },
  { label: "Notes", value: f.notes },
  { label: "Attachments", value: attachments.value.length ? String(attachments.value.length) : "" },
])

function askSave() {
  error.value = ""
  if (!f.customer) { error.value = "Choose a customer first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  confirming.value = true
}

async function save() {
  error.value = ""
  if (!f.customer) { error.value = "Choose a customer first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  saving.value = true
  try {
    const r = await call("kayanick_crm.case_api.create_case", {
      payload: JSON.stringify({
        customer: f.customer.name, case_date: f.case_date, attended: f.attended, notes: f.notes,
        products: f.products,
      }),
    }, { post: true })
    const failed = attachments.value.length ? await uploadFiles("KC Case", r.case, attachments.value) : []
    if (failed.length) alert("Case saved, but these files failed to upload:\n" + failed.join("\n"))
    confirming.value = false
    router.push({ name: "cases", query: { saved: r.case } })
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
          <button type="button" class="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2.5" @click="f.attended = !f.attended">
            <span class="text-left">
              <span class="block text-sm font-medium">Attended</span>
              <span class="block text-xs text-gray-400">{{ f.attended ? "Case is done" : "Planned — shows in Today until marked attended" }}</span>
            </span>
            <span class="relative h-6 w-11 shrink-0 rounded-full transition" :class="f.attended ? 'bg-brand-600' : 'bg-gray-200'">
              <span class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all" :class="f.attended ? 'left-[22px]' : 'left-0.5'"></span>
            </span>
          </button>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="clipboard" :size="14" />Products<span v-if="f.products.length" class="text-gray-400">· {{ f.products.length }}</span></p>
        <div class="card p-4">
          <div class="flex flex-wrap gap-2">
            <button v-for="p in productOptions" :key="p" type="button" class="chip"
              :class="f.products.includes(p) ? 'border-brand-600 bg-brand-50 text-brand-700' : ''" @click="toggleProduct(p)">
              <Icon v-if="f.products.includes(p)" name="check" :size="13" />{{ p }}
            </button>
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
          {{ saving ? (attachments.length ? "Saving & uploading…" : "Saving…") : "Save case" }}
        </button>
      </div>
    </div>

    <ConfirmSheet v-model:open="confirming" title="Save this case?" :rows="summary" confirm-text="Save case"
      :busy="saving" @confirm="save" />
    <PickerSheet v-model:open="customerOpen" title="Choose customer" placeholder="Search customers"
      :fetcher="fetchCustomers" @pick="(r) => (f.customer = r.raw)" />
  </div>
</template>
