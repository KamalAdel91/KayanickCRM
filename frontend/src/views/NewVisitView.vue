<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { localToday, outcomeBadge, levelBadge, chipOn, dot } from "../ui"
import Icon from "../components/Icon.vue"
import AttachPicker from "../components/AttachPicker.vue"
import PickerSheet from "../components/PickerSheet.vue"
import PickField from "../components/PickField.vue"
import ConfirmSheet from "../components/ConfirmSheet.vue"
import { uploadFiles } from "../upload"

const route = useRoute()
const router = useRouter()
const opts = ref({ purposes: [], outcomes: [], levels: [], products: [] })
const f = reactive({
  hospital: "", hospitalSub: "", doctor: null, visit_date: localToday(), purpose: "", outcome: "", level: "",
  products: [], order: false, notes: "", next_action: "", next_visit_date: "",
})
const levelTouched = ref(false)
const doctors = ref([])
const sheet = ref("")
const geo = ref(null)
const geoState = ref("locating")
const saving = ref(false)
const attachments = ref([])
const confirming = ref(false)
const error = ref("")

const geoLabel = computed(() => (geo.value ? "Location on" : geoState.value === "locating" ? "Locating…" : "No location"))
const hospitalOpen = computed({ get: () => sheet.value === "hospital", set: (v) => (sheet.value = v ? "hospital" : "") })
const doctorOpen = computed({ get: () => sheet.value === "doctor", set: (v) => (sheet.value = v ? "doctor" : "") })

async function fetchHospitals(text) {
  const r = await call("kayanick_crm.mobile.search", { text })
  return r.hospitals.map((h) => ({ value: h.name, label: h.name, sub: [h.area, h.hospital_type].filter(Boolean).join(" · "), raw: h }))
}
async function fetchDoctors(text) {
  const t = (text || "").toLowerCase()
  return doctors.value
    .filter((d) => !t || d.doctor_name.toLowerCase().includes(t))
    .map((d) => ({ value: d.name, label: d.doctor_name, sub: d.relationship_level || "", raw: d }))
}
async function loadDoctors() {
  doctors.value = []
  if (!f.hospital) return
  try { doctors.value = await call("kayanick_crm.mobile.get_doctors", { hospital: f.hospital }) }
  catch (e) { error.value = e.message }
}
function pickHospital(r) {
  f.hospital = r.value
  f.hospitalSub = r.sub
  f.doctor = null
  loadDoctors().then(() => { if (!f.doctor) sheet.value = "doctor" })
}
function clearHospital() {
  f.hospital = ""
  f.hospitalSub = ""
  f.doctor = null
  doctors.value = []
}
function pickDoctor(d) {
  f.doctor = d || null
  if (d && d.relationship_level && !levelTouched.value) f.level = d.relationship_level
}
function openDoctors() {
  if (!f.hospital) { sheet.value = "hospital"; return }
  sheet.value = "doctor"
}
function pickLevel(l) {
  levelTouched.value = true
  f.level = f.level === l ? "" : l
}
function toggleProduct(p) {
  const i = f.products.indexOf(p)
  if (i >= 0) f.products.splice(i, 1)
  else f.products.push(p)
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/")
}
onMounted(async () => {
  try { opts.value = await call("kayanick_crm.mobile.get_options") }
  catch (e) { error.value = e.message }
  if (route.query.hospital) {
    f.hospital = route.query.hospital
    await loadDoctors()
    if (route.query.doctor) pickDoctor(doctors.value.find((d) => d.name === route.query.doctor))
  }
  if (!navigator.geolocation) { geoState.value = "unsupported"; return }
  navigator.geolocation.getCurrentPosition(
    (pos) => { geo.value = { lat: pos.coords.latitude, lng: pos.coords.longitude, acc: pos.coords.accuracy } },
    () => { geoState.value = "denied" },
    { enableHighAccuracy: true, timeout: 10000 },
  )
})

const summary = computed(() => [
  { label: "Hospital", value: f.hospital },
  { label: "Doctor", value: f.doctor ? f.doctor.doctor_name : "" },
  { label: "Date", value: f.visit_date },
  { label: "Purpose", value: f.purpose },
  { label: "Outcome", value: f.outcome },
  { label: "Relationship", value: f.level },
  { label: "Products", value: f.products.join(", ") },
  { label: "Order expected", value: f.order ? "Yes" : "" },
  { label: "Notes", value: f.notes },
  { label: "Next action", value: f.next_action },
  { label: "Next visit", value: f.next_visit_date },
  { label: "Attachments", value: attachments.value.length ? String(attachments.value.length) : "" },
])

function askSave() {
  error.value = ""
  if (!f.hospital) { error.value = "Choose a hospital first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  if (!f.doctor) { error.value = "Choose a doctor"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  confirming.value = true
}

async function save() {
  error.value = ""
  if (!f.hospital) { error.value = "Choose a hospital first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  if (!f.doctor) { error.value = "Choose a doctor"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  const payload = {
    hospital: f.hospital, doctor: f.doctor ? f.doctor.name : "", visit_date: f.visit_date,
    visit_purpose: f.purpose, visit_outcome: f.outcome, relationship_level: f.level,
    products: f.products, order_expected: f.order, notes: f.notes,
    next_action: f.next_action, next_visit_date: f.next_visit_date,
  }
  if (geo.value) {
    payload.geolocation = JSON.stringify({
      type: "FeatureCollection",
      features: [{
        type: "Feature",
        properties: { point_type: "circle", radius: geo.value.acc || 10 },
        geometry: { type: "Point", coordinates: [geo.value.lng, geo.value.lat] },
      }],
    })
  }
  saving.value = true
  try {
    const r = await call("kayanick_crm.mobile.create_visit", { payload: JSON.stringify(payload) }, { post: true })
    const failed = attachments.value.length ? await uploadFiles("KC Visit", r.name, attachments.value) : []
    if (failed.length) alert("Visit saved, but these files failed to upload:\n" + failed.join("\n"))
    confirming.value = false
    router.push({ name: "today", query: { saved: r.name } })
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
        <h1 class="page-title flex-1">New visit</h1>
        <span class="badge" :class="geo ? 'badge-green' : 'badge-gray'"><Icon name="map-pin" :size="12" />{{ geoLabel }}</span>
      </div>
    </header>

    <form id="visitform" class="wrap space-y-5 py-4" @submit.prevent="askSave">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <section>
        <p class="section-label"><Icon name="building" :size="14" />Hospital &amp; doctor</p>
        <div class="card space-y-4 p-4">
          <div>
            <label class="label">Hospital</label>
            <PickField :value="f.hospital" :sub="f.hospitalSub" icon="building" placeholder="Choose hospital"
              @open="sheet = 'hospital'" @clear="clearHospital" />
          </div>
          <div>
            <label class="label">Doctor</label>
            <PickField :value="f.doctor ? f.doctor.doctor_name : ''" :sub="f.doctor ? f.doctor.relationship_level : ''" icon="user"
              :placeholder="f.hospital ? 'Choose doctor (' + doctors.length + ')' : 'Choose the hospital first'"
              @open="openDoctors" @clear="pickDoctor(null)" />
          </div>
          <div>
            <label class="label">Date</label>
            <input v-model="f.visit_date" type="date" class="input" required />
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="clipboard" :size="14" />Visit</p>
        <div class="card space-y-4 p-4">
          <div>
            <label class="label">Visit purpose</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="p in opts.purposes" :key="p" type="button" class="chip" :class="{ 'chip-on': f.purpose === p }"
                @click="f.purpose = f.purpose === p ? '' : p">{{ p }}</button>
            </div>
          </div>
          <div>
            <label class="label">Visit outcome</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="o in opts.outcomes" :key="o" type="button" class="chip" :class="f.outcome === o ? chipOn(outcomeBadge(o)) : ''"
                @click="f.outcome = f.outcome === o ? '' : o">
                <span class="h-2 w-2 rounded-full" :class="dot(outcomeBadge(o))"></span>{{ o }}
              </button>
            </div>
          </div>
          <div>
            <label class="label">Relationship level</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="l in opts.levels" :key="l" type="button" class="chip" :class="f.level === l ? chipOn(levelBadge(l)) : ''" @click="pickLevel(l)">
                <span class="h-2 w-2 rounded-full" :class="dot(levelBadge(l))"></span>{{ l }}
              </button>
            </div>
          </div>
          <div>
            <label class="label">Product discussed</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="p in opts.products" :key="p" type="button" class="chip"
                :class="f.products.includes(p) ? 'border-brand-600 bg-brand-50 text-brand-700' : ''" @click="toggleProduct(p)">
                <Icon v-if="f.products.includes(p)" name="check" :size="13" />{{ p }}
              </button>
            </div>
          </div>
          <button type="button" class="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2.5" @click="f.order = !f.order">
            <span class="flex items-center gap-2 text-sm font-medium"><Icon name="cart" :size="16" class="text-gray-500" />Order expected</span>
            <span class="relative h-6 w-11 rounded-full transition" :class="f.order ? 'bg-brand-600' : 'bg-gray-200'">
              <span class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all" :class="f.order ? 'left-[22px]' : 'left-0.5'"></span>
            </span>
          </button>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
        <div class="card p-4">
          <textarea v-model="f.notes" rows="5" placeholder="What happened in the visit?" class="input h-auto resize-none py-2" dir="auto"></textarea>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="flag" :size="14" />Next step</p>
        <div class="card space-y-3 p-4">
          <textarea v-model="f.next_action" rows="2" placeholder="Next action" class="input h-auto resize-none py-2" dir="auto"></textarea>
          <div>
            <label class="label">Next visit date</label>
            <input v-model="f.next_visit_date" type="date" class="input" />
          </div>
        </div>
      </section>

      <section>
        <p class="section-label"><Icon name="paperclip" :size="14" />Attachments<span v-if="attachments.length" class="text-gray-400">· {{ attachments.length }}</span></p>
        <div class="card p-4"><AttachPicker v-model="attachments" /></div>
      </section>
    </form>

    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="wrap py-3">
        <button form="visitform" type="submit" class="btn btn-primary h-11 w-full text-[15px]" :disabled="saving">
          {{ saving ? (attachments.length ? "Saving & uploading…" : "Saving…") : "Save visit" }}
        </button>
      </div>
    </div>

    <ConfirmSheet v-model:open="confirming" title="Save this visit?" :rows="summary" confirm-text="Save visit"
      note="You won't be able to delete it after saving." :busy="saving" @confirm="save" />
    <PickerSheet v-model:open="hospitalOpen" title="Choose hospital" placeholder="Search hospitals or areas"
      :fetcher="fetchHospitals" @pick="pickHospital" />
    <PickerSheet v-model:open="doctorOpen" title="Choose doctor" placeholder="Search doctors"
      :fetcher="fetchDoctors" @pick="(r) => pickDoctor(r.raw)" />
  </div>
</template>
