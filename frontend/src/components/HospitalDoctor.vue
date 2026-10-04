<script setup>
import { ref, computed, onMounted } from "vue"
import { call } from "../api"
import { getOptions } from "../options"
import PickerSheet from "./PickerSheet.vue"
import PickField from "./PickField.vue"
import AddSheet from "./AddSheet.vue"
import Icon from "./Icon.vue"

// hospital: name (string); doctors: [{ name, doctor_name, relationship_level }]
const hospital = defineModel("hospital", { type: String, default: "" })
const hospitalSub = defineModel("hospitalSub", { type: String, default: "" })
const doctors = defineModel("doctors", { type: Array, default: () => [] })
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
  if (!doctors.value.length) sheet.value = "doctor"
}
function pickDoctor(r) {
  if (!r || !r.raw) return
  if (doctors.value.some((d) => d.name === r.raw.name)) return
  doctors.value = [...doctors.value, r.raw]
  emit("doctor-picked", r.raw)
}
function removeDoctor(name) {
  doctors.value = doctors.value.filter((d) => d.name !== name)
}
</script>

<template>
  <div>
    <label class="label">Hospital</label>
    <PickField :value="hospital" :sub="hospitalSub" icon="building" placeholder="Choose hospital"
      @open="sheet = 'hospital'" @clear="hospital = ''; hospitalSub = ''" />
  </div>
  <div>
    <label class="label">Doctors<span class="text-red-500"> *</span><span v-if="doctors.length" class="text-gray-400"> · {{ doctors.length }}</span></label>
    <div class="space-y-2">
      <div v-for="d in doctors" :key="d.name" class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2">
        <Icon name="user" :size="16" class="shrink-0 text-gray-400" />
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm font-medium" dir="auto">{{ d.doctor_name }}</span>
          <span v-if="d.relationship_level" class="block text-xs text-gray-400">{{ d.relationship_level }}</span>
        </span>
        <button type="button" class="p-1 text-gray-400" aria-label="Remove doctor" @click="removeDoctor(d.name)"><Icon name="x" :size="16" /></button>
      </div>
      <button type="button" class="btn btn-subtle h-10 w-full" @click="sheet = 'doctor'">
        <Icon name="plus" :size="15" />{{ doctors.length ? "Add another doctor" : "Choose doctor" }}
      </button>
    </div>
  </div>
  <PickerSheet v-model:open="hospitalOpen" title="Choose hospital" placeholder="Search hospitals or areas"
    :fetcher="fetchHospitals" :create-label="opts.can_add_hospital ? 'Add hospital' : ''"
    @pick="pickHospital" @create="(t) => startAdd('hospital', t)" />
  <PickerSheet v-model:open="doctorOpen" title="Choose doctor" placeholder="Search doctors"
    :fetcher="fetchDoctors" :create-label="opts.can_add_doctor ? 'Add doctor' : ''"
    @pick="pickDoctor" @create="(t) => startAdd('doctor', t)" />
  <AddSheet v-model:open="addOpen" :kind="adding || 'hospital'" :initial="addText" :options="opts" @added="added" />
</template>
