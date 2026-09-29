<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import Icon from "../components/Icon.vue"

const PRODUCTS = ["IVL", "IVUS", "Physiology", "Renal Denervation", "Other"]
const VISIT_TYPES = [
  ["Face to Face", "user"], ["Phone", "phone"], ["WhatsApp", "message"],
  ["Email", "mail"], ["Online Meeting", "video"], ["Conference", "users"],
]
const INTEREST = [
  ["Very Positive", "bg-green-600", "border-green-600 bg-green-50 text-green-800"],
  ["Positive", "bg-green-400", "border-green-500 bg-green-50 text-green-800"],
  ["Neutral", "bg-gray-400", "border-gray-500 bg-gray-100 text-gray-800"],
  ["Negative", "bg-red-500", "border-red-500 bg-red-50 text-red-700"],
  ["No Decision", "bg-amber-500", "border-amber-500 bg-amber-50 text-amber-800"],
  ["Not Available", "bg-gray-300", "border-gray-400 bg-gray-100 text-gray-600"],
]

const route = useRoute()
const router = useRouter()
const f = reactive({
  hospital: "", hospitalTitle: "", doctor: "", visit_type: "Face to Face", interest: "",
  products: [], purpose: "", notes: "", next_action: "", due_date: "", next_visit_date: "",
})
const q = ref("")
const hits = ref([])
const doctors = ref([])
const geo = ref(null)
const geoState = ref("locating")
const saving = ref(false)
const error = ref("")
let timer = null

const geoLabel = computed(() => (geo.value ? "Location on" : geoState.value === "locating" ? "Locating…" : "No location"))

function initials(s) {
  return (s || "?").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase()
}
async function loadDoctors() {
  doctors.value = []
  if (!f.hospital) return
  try { doctors.value = await call("kayanick_crm.mobile.get_doctors", { hospital: f.hospital }) }
  catch (e) { error.value = e.message }
}
function pick(h) {
  f.hospital = h.name
  f.hospitalTitle = h.account_name
  f.doctor = ""
  hits.value = []
  q.value = ""
  loadDoctors()
}
function clearHospital() {
  f.hospital = ""
  f.hospitalTitle = ""
  f.doctor = ""
  doctors.value = []
}
watch(q, (v) => {
  clearTimeout(timer)
  if (!v || v.length < 2) { hits.value = []; return }
  timer = setTimeout(async () => {
    try { hits.value = (await call("kayanick_crm.mobile.search", { text: v })).accounts }
    catch (e) { error.value = e.message }
  }, 300)
})
function toggle(p) {
  const i = f.products.indexOf(p)
  if (i >= 0) f.products.splice(i, 1)
  else f.products.push(p)
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/")
}
onMounted(() => {
  if (route.query.hospital) {
    f.hospital = route.query.hospital
    f.hospitalTitle = route.query.title || route.query.hospital
    loadDoctors()
  }
  if (!navigator.geolocation) { geoState.value = "unsupported"; return }
  navigator.geolocation.getCurrentPosition(
    (pos) => { geo.value = { lat: pos.coords.latitude, lng: pos.coords.longitude, acc: pos.coords.accuracy } },
    () => { geoState.value = "denied" },
    { enableHighAccuracy: true, timeout: 10000 },
  )
})

async function save() {
  error.value = ""
  if (!f.hospital) { error.value = "Choose a hospital first"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  const payload = {
    hospital_account: f.hospital, doctor: f.doctor, visit_type: f.visit_type,
    doctor_interest_level: f.interest, products_discussed: f.products.join(", "),
    purpose: f.purpose, visit_notes: f.notes, next_action: f.next_action,
    due_date: f.due_date, next_visit_date: f.next_visit_date,
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
    router.push({ name: "today", query: { saved: r.name } })
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
        <h1 class="page-title flex-1">New visit</h1>
        <span class="badge" :class="geo ? 'badge-green' : 'badge-gray'"><Icon name="map-pin" :size="12" />{{ geoLabel }}</span>
      </div>
    </header>

    <form id="visitform" class="wrap space-y-5 py-4" @submit.prevent="save">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <section>
        <p class="section-label flex items-center gap-1.5"><Icon name="building" :size="14" />Hospital &amp; doctor</p>
        <div class="card space-y-4 p-4">
          <div>
            <label class="label">Hospital</label>
            <div v-if="f.hospital" class="flex items-center gap-3 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2">
              <span class="avatar h-8 w-8 bg-white text-brand-700">{{ initials(f.hospitalTitle) }}</span>
              <span class="flex-1 truncate font-medium" dir="auto">{{ f.hospitalTitle }}</span>
              <button type="button" class="text-sm font-medium text-brand-700" @click="clearHospital">Change</button>
            </div>
            <template v-else>
              <div class="relative">
                <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
                <input v-model="q" type="search" placeholder="Type at least 2 letters" class="input pl-9" dir="auto" />
              </div>
              <div v-if="hits.length" class="card mt-2 divide-y divide-gray-100 overflow-hidden">
                <button v-for="h in hits" :key="h.name" type="button" class="flex w-full items-center gap-3 px-3 py-2.5 text-left active:bg-gray-50" @click="pick(h)">
                  <span class="avatar h-8 w-8">{{ initials(h.account_name) }}</span>
                  <span class="flex-1 truncate" dir="auto">{{ h.account_name }}</span>
                  <span class="text-xs text-gray-400">{{ h.city }}</span>
                </button>
              </div>
            </template>
          </div>

          <div v-if="f.hospital">
            <label class="label">Doctor</label>
            <p v-if="!doctors.length" class="text-sm text-gray-400">No doctors on file for this hospital</p>
            <div v-else class="flex flex-wrap gap-2">
              <button type="button" class="chip" :class="{ 'chip-on': !f.doctor }" @click="f.doctor = ''">None</button>
              <button v-for="d in doctors" :key="d.name" type="button" class="chip inline-flex items-center gap-1.5"
                :class="{ 'chip-on': f.doctor === d.name }" dir="auto" @click="f.doctor = d.name">
                <Icon name="user" :size="13" />{{ d.doctor_name }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label flex items-center gap-1.5"><Icon name="clipboard" :size="14" />Visit details</p>
        <div class="card space-y-4 p-4">
          <div>
            <label class="label">Type</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="[v, ic] in VISIT_TYPES" :key="v" type="button" class="chip inline-flex items-center gap-1.5"
                :class="{ 'chip-on': f.visit_type === v }" @click="f.visit_type = v">
                <Icon :name="ic" :size="14" />{{ v }}
              </button>
            </div>
          </div>
          <div>
            <label class="label">Products discussed</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="p in PRODUCTS" :key="p" type="button" class="chip inline-flex items-center gap-1.5"
                :class="f.products.includes(p) ? 'border-brand-600 bg-brand-50 text-brand-700' : ''" @click="toggle(p)">
                <Icon v-if="f.products.includes(p)" name="check" :size="13" />{{ p }}
              </button>
            </div>
          </div>
          <div>
            <label class="label">Doctor interest</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="[i, dot, on] in INTEREST" :key="i" type="button" class="chip inline-flex items-center gap-2"
                :class="f.interest === i ? on : ''" @click="f.interest = f.interest === i ? '' : i">
                <span class="h-2 w-2 rounded-full" :class="dot"></span>{{ i }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section>
        <p class="section-label flex items-center gap-1.5"><Icon name="file-text" :size="14" />Notes</p>
        <div class="card space-y-3 p-4">
          <input v-model="f.purpose" placeholder="Purpose of the visit" class="input" dir="auto" />
          <textarea v-model="f.notes" rows="4" placeholder="What happened, what did you learn?" class="input h-auto resize-none py-2" dir="auto"></textarea>
        </div>
      </section>

      <section>
        <p class="section-label flex items-center gap-1.5"><Icon name="flag" :size="14" />Next step</p>
        <div class="card space-y-3 p-4">
          <input v-model="f.next_action" placeholder="e.g. Send IVL quotation" class="input" dir="auto" />
          <div class="grid grid-cols-2 gap-3">
            <div><label class="label">Action due</label><input v-model="f.due_date" type="date" class="input" /></div>
            <div><label class="label">Next visit</label><input v-model="f.next_visit_date" type="date" class="input" /></div>
          </div>
          <p v-if="f.next_action && f.due_date" class="flex items-center gap-1.5 text-xs text-green-700">
            <Icon name="check" :size="13" />A follow-up task will be created
          </p>
        </div>
      </section>
    </form>

    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="wrap py-3">
        <button form="visitform" type="submit" class="btn btn-primary h-11 w-full text-[15px]" :disabled="saving">
          {{ saving ? "Saving…" : "Save visit" }}
        </button>
      </div>
    </div>
  </div>
</template>
