<script setup>
import { ref, computed, onMounted } from "vue"
import { call } from "../api"
import { getOptions } from "../options"
import PickerSheet from "./PickerSheet.vue"
import PickField from "./PickField.vue"
import AddSheet from "./AddSheet.vue"

// hospital: name (string); doctor: { name, doctor_name, relationship_level } | null
const hospital = defineModel("hospital", { type: String, default: "" })
const hospitalSub = defineModel("hospitalSub", { type: String, default: "" })
const doctor = defineModel("doctor", { type: Object, default: null })
const emit = defineEmits(["doctor-picked"])

const sheet = ref("")
const hospitalOpen = computed({ get: () => sheet.value === "hospital", set: (v) => (sheet.value = v ? "hospital" : "") })
const doctorOpen = computed({ get: () => sheet.value === "doctor", set: (v) => (sheet.value = v ? "doctor" : "") })

async function fetchHospitals(text) {
  const r = await call("kayanick_crm.mobile.search", { text })
  return r.hospitals.map((h) => ({ value: h.name, label: h.name, sub: [h.area, h.hospital_type].filter(Boolean).join(" · "), raw: h }))
}
async function fetchDoctors(text) {
  const r = await call("kayanick_crm.mobile.search", { text })
  return r.doctors.map((d) => ({ value: d.name, label: d.doctor_name, sub: d.relationship_level || "", raw: d }))
}
// admins / sales managers can add a missing hospital or doctor from the picker
const opts = ref({})
onMounted(async () => { try { opts.value = await getOptions() } catch (e) {} })
const adding = ref("")
const addText = ref("")
const addOpen = computed({ get: () => !!adding.value, set: (v) => { if (!v) adding.value = "" } })
function startAdd(kind, text) {
  addText.value = text || ""
  adding.value = kind
}
function added(r) {
  if (adding.value === "hospital") {
    pickHospital({ value: r.name, sub: [r.area, r.hospital_type].filter(Boolean).join(" · ") })
  } else {
    pickDoctor({ raw: r })
  }
}
function pickHospital(r) {
  hospital.value = r.value
  hospitalSub.value = r.sub
  if (!doctor.value) sheet.value = "doctor"
}
function pickDoctor(r) {
  doctor.value = r ? r.raw : null
  if (r) emit("doctor-picked", r.raw)
}
</script>

<template>
  <div>
    <label class="label">Hospital</label>
    <PickField :value="hospital" :sub="hospitalSub" icon="building" placeholder="Choose hospital"
      @open="sheet = 'hospital'" @clear="hospital = ''; hospitalSub = ''" />
  </div>
  <div>
    <label class="label">Doctor</label>
    <PickField :value="doctor ? doctor.doctor_name : ''" :sub="doctor ? doctor.relationship_level : ''" icon="user"
      placeholder="Choose doctor" @open="sheet = 'doctor'" @clear="doctor = null" />
  </div>
  <PickerSheet v-model:open="hospitalOpen" title="Choose hospital" placeholder="Search hospitals or areas"
    :fetcher="fetchHospitals" :create-label="opts.can_add_hospital ? 'Add hospital' : ''"
    @pick="pickHospital" @create="(t) => startAdd('hospital', t)" />
  <PickerSheet v-model:open="doctorOpen" title="Choose doctor" placeholder="Search doctors"
    :fetcher="fetchDoctors" :create-label="opts.can_add_doctor ? 'Add doctor' : ''"
    @pick="pickDoctor" @create="(t) => startAdd('doctor', t)" />
  <AddSheet v-model:open="addOpen" :kind="adding || 'hospital'" :initial="addText" :options="opts" @added="added" />
</template>
