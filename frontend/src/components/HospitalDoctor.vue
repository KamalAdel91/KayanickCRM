<script setup>
import { ref, computed } from "vue"
import { call } from "../api"
import PickerSheet from "./PickerSheet.vue"
import PickField from "./PickField.vue"

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
    :fetcher="fetchHospitals" @pick="pickHospital" />
  <PickerSheet v-model:open="doctorOpen" title="Choose doctor" placeholder="Search doctors"
    :fetcher="fetchDoctors" @pick="pickDoctor" />
</template>
