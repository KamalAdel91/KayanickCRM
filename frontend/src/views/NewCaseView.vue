<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmtTime, localToday, usedItemsError, usedItemsText } from "../ui"
import Icon from "../components/Icon.vue"
import AttachPicker from "../components/AttachPicker.vue"
import HospitalDoctor from "../components/HospitalDoctor.vue"
import ConfirmSheet from "../components/ConfirmSheet.vue"
import UsedItems from "../components/UsedItems.vue"
import AttendeePick from "../components/AttendeePick.vue"
import { uploadDetached } from "../upload"

const route = useRoute()
const router = useRouter()
const f = reactive({ hospital: "", hospitalSub: "", doctors: [], case_date: localToday(), case_time: "", attended: true, notes: "", products: [], used_products: "", used_items: [], attended_by: null })
const productOptions = ref([])
watch(() => f.case_date, (d) => { f.attended = !!d && d <= localToday() })
const saving = ref(false)
const attachments = ref([])
const uploaded = new Map()  // attachment -> File name, kept across retries
const confirming = ref(false)
const error = ref("")

const canSave = computed(() => !saving.value)
function toggleProduct(p) {
  const i = f.products.indexOf(p)
  if (i >= 0) f.products.splice(i, 1)
  else f.products.push(p)
}
onMounted(async () => {
  try { productOptions.value = (await call("kayanick_crm.mobile.get_options")).products }
  catch (e) { error.value = e.message }
  if (route.query.hospital) f.hospital = route.query.hospital
  if (route.query.doctor) {
    try {
      const d = await call("kayanick_crm.mobile.get_doctor", { name: route.query.doctor })
      if (d) f.doctors = [d]
    } catch (e) {}
  }
})
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/cases")
}

const summary = computed(() => [
  { label: "Hospital", value: f.hospital },
  { label: f.doctors.length > 1 ? "Doctors" : "Doctor", value: f.doctors.map((d) => d.doctor_name).join(", ") },
  { label: "Case date", value: f.case_date },
  { label: "Time", value: fmtTime(f.case_time) },
  { label: "Status", value: f.attended ? "Attended" : "Planned (follow-up)" },
  { label: "Products", value: f.products.join(", ") },
  { label: "Attended by", value: f.attended ? (f.attended_by ? f.attended_by.full_name || f.attended_by.name : "Me") : "" },
  { label: "Used products", value: f.attended ? f.used_products : "" },
  { label: "Used items", value: f.attended && f.used_products === "Yes" ? usedItemsText(f.used_items) : "" },
  { label: "Notes", value: f.notes },
  { label: "Attachments", value: attachments.value.length ? String(attachments.value.length) : "" },
])

function askSave() {
  error.value = ""
  if (!f.hospital) { error.value = "Choose a hospital first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  if (!f.doctors.length) { error.value = "Choose at least one doctor"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  const req = !f.case_date ? "Choose the case date" : !f.case_time ? "Choose the case time" : !f.products.length ? "Choose at least one product" : !f.notes.trim() ? "Write the notes" : ""
  if (req) { error.value = req; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  const usedErr = f.attended ? usedItemsError(f.used_products, f.used_items) : ""
  if (usedErr) { error.value = usedErr; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  confirming.value = true
}

async function save() {
  error.value = ""
  saving.value = true
  try {
    // files go up first: a case attended by someone else belongs to him, and its creator can't add files later
    const up = attachments.value.length ? await uploadDetached(attachments.value, uploaded) : { names: [], failed: [] }
    const r = await call("kayanick_crm.case_api.create_case", {
      payload: JSON.stringify({
        hospital: f.hospital, doctors: f.doctors.map((d) => d.name), case_date: f.case_date, case_time: f.case_time, attended: f.attended, notes: f.notes,
        products: f.products,
        attended_by: f.attended && f.attended_by ? f.attended_by.name : "",
        used_products: f.attended ? f.used_products : "",
        used_items: f.attended && f.used_products === "Yes" ? f.used_items.map((r) => ({ item_code: r.item_code, qty: r.qty })) : [],
        files: up.names,
      }),
    }, { post: true })
    if (up.failed.length) alert("Case saved, but these files failed to upload:\n" + up.failed.join("\n"))
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
        <p class="section-label"><Icon name="building" :size="14" />Hospital &amp; doctor</p>
        <div class="card space-y-4 p-4">
          <HospitalDoctor v-model:hospital="f.hospital" v-model:hospital-sub="f.hospitalSub" v-model:doctors="f.doctors" />
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Case date<span class="text-red-500"> *</span></label>
              <input v-model="f.case_date" type="date" class="input" />
            </div>
            <div>
              <label class="label">Time<span class="text-red-500"> *</span></label>
              <input v-model="f.case_time" type="time" class="input" />
            </div>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="clipboard" :size="14" />Products<span class="text-red-500"> *</span><span v-if="f.products.length" class="text-gray-400">· {{ f.products.length }}</span></p>
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
        <p class="section-label"><Icon name="check" :size="14" />Status</p>
        <div class="card space-y-4 p-4">
          <button type="button" class="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2.5" @click="f.attended = !f.attended">
            <span class="text-left">
              <span class="block text-sm font-medium">Attended</span>
              <span class="block text-xs text-gray-400">{{ f.attended ? "Case is done" : "Planned — shows in Today until marked attended" }}</span>
            </span>
            <span class="relative h-6 w-11 shrink-0 rounded-full transition" :class="f.attended ? 'bg-brand-600' : 'bg-gray-200'">
              <span class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all" :class="f.attended ? 'left-[22px]' : 'left-0.5'"></span>
            </span>
          </button>
          <AttendeePick v-if="f.attended" v-model="f.attended_by" />
          <UsedItems v-if="f.attended" v-model:used="f.used_products" v-model:items="f.used_items" />
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="file-text" :size="14" />Notes<span class="text-red-500"> *</span></p>
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
  </div>
</template>
