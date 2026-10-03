<script setup>
import { ref, reactive, watch } from "vue"
import { call } from "../api"
import Icon from "./Icon.vue"

// kind: "hospital" | "doctor". Emits "added" with the new record.
const props = defineProps({
  open: Boolean,
  kind: { type: String, default: "hospital" },
  initial: { type: String, default: "" },
  options: { type: Object, default: () => ({}) },
})
const emit = defineEmits(["update:open", "added"])
const f = reactive({ name: "", area: "", hospital_type: "", relationship_level: "" })
const saving = ref(false)
const error = ref("")

watch(() => props.open, (v) => {
  document.body.style.overflow = v ? "hidden" : ""
  if (!v) return
  Object.assign(f, { name: props.initial || "", area: "", hospital_type: "", relationship_level: "" })
  error.value = ""
})
function close() { if (!saving.value) emit("update:open", false) }

async function save() {
  error.value = ""
  if (!f.name.trim()) { error.value = props.kind === "hospital" ? "Write the hospital name" : "Write the doctor name"; return }
  saving.value = true
  try {
    const r = props.kind === "hospital"
      ? await call("kayanick_crm.mobile.create_hospital", { hospital_name: f.name, area: f.area, hospital_type: f.hospital_type }, { post: true })
      : await call("kayanick_crm.mobile.create_doctor", { doctor_name: f.name, relationship_level: f.relationship_level }, { post: true })
    emit("added", r)
    emit("update:open", false)
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
</script>

<template>
  <teleport to="body">
    <transition name="sheet-fade">
      <div v-if="open" class="fixed inset-0 z-[60] bg-black/40" @click="close"></div>
    </transition>
    <transition name="sheet-up">
      <div v-if="open" class="fixed inset-x-0 bottom-0 z-[70] mx-auto flex max-h-[85vh] max-w-lg flex-col rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)] shadow-2xl">
        <div class="flex justify-center pt-2"><span class="h-1 w-10 rounded-full bg-gray-300"></span></div>
        <div class="flex items-center gap-3 px-4 pb-2 pt-2">
          <h2 class="flex-1 text-base font-semibold">{{ kind === "hospital" ? "New hospital" : "New doctor" }}</h2>
          <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Close" @click="close"><Icon name="x" :size="16" /></button>
        </div>
        <div class="flex-1 space-y-4 overflow-y-auto px-4 pb-2">
          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
          <div>
            <label class="label">{{ kind === "hospital" ? "Hospital name" : "Doctor name" }}<span class="text-red-500"> *</span></label>
            <input v-model="f.name" type="text" class="input" dir="auto"
              :placeholder="kind === 'hospital' ? 'e.g. EGY Heart' : 'e.g. Ahmed Ali'" />
            <p v-if="kind === 'doctor'" class="mt-1 text-xs text-gray-400">Saved as “Dr. First Last”</p>
          </div>
          <template v-if="kind === 'hospital'">
            <div v-if="options.areas && options.areas.length">
              <label class="label">Area</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="a in options.areas" :key="a" type="button" class="chip" :class="{ 'chip-on': f.area === a }"
                  @click="f.area = f.area === a ? '' : a">{{ a }}</button>
              </div>
            </div>
            <div v-if="options.hospital_types && options.hospital_types.length">
              <label class="label">Type</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="t in options.hospital_types" :key="t" type="button" class="chip" :class="{ 'chip-on': f.hospital_type === t }"
                  @click="f.hospital_type = f.hospital_type === t ? '' : t">{{ t }}</button>
              </div>
            </div>
          </template>
          <div v-else-if="options.levels && options.levels.length">
            <label class="label">Relationship level</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="l in options.levels" :key="l" type="button" class="chip" :class="{ 'chip-on': f.relationship_level === l }"
                @click="f.relationship_level = f.relationship_level === l ? '' : l">{{ l }}</button>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 p-4">
          <button type="button" class="btn btn-subtle h-11" :disabled="saving" @click="close">Cancel</button>
          <button type="button" class="btn btn-primary h-11" :disabled="saving" @click="save">{{ saving ? "Saving…" : "Add" }}</button>
        </div>
      </div>
    </transition>
  </teleport>
</template>
