<script setup>
import { ref, computed, onMounted } from "vue"
import { call } from "../api"
import Icon from "./Icon.vue"

// kind: "visits" | "cases"
const props = defineProps({ kind: { type: String, default: "visits" } })
const f = defineModel({ type: Object, required: true })
const open = ref(false)
const team = ref([])

const statusOptions = computed(() => (props.kind === "visits"
  ? [{ label: "Positive", key: "outcome", value: "Positive" }, { label: "Negative", key: "outcome", value: "Negative" }]
  : [{ label: "Planned", key: "attended", value: 0 }, { label: "Attended", key: "attended", value: 1 }]))
const active = computed(() => ["from_date", "to_date", "sales_rep", "outcome", "attended"]
  .filter((k) => f.value[k] !== "" && f.value[k] !== undefined && f.value[k] !== null).length)

function toggleStatus(o) {
  f.value[o.key] = f.value[o.key] === o.value ? "" : o.value
}
function clear() {
  Object.assign(f.value, { from_date: "", to_date: "", sales_rep: "", outcome: "", attended: "" })
}
onMounted(async () => {
  try { team.value = await call("kayanick_crm.mobile.get_team") } catch (e) {}
})
</script>

<template>
  <div class="space-y-2">
    <div class="flex gap-2">
      <div class="relative flex-1">
        <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
        <input v-model="f.text" type="search" placeholder="Hospital or doctor" class="input pl-9" dir="auto" />
      </div>
      <button type="button" class="btn relative h-10" :class="open || active ? 'btn-primary' : 'btn-subtle'" @click="open = !open">
        Filters<span v-if="active" class="ml-0.5 rounded-full bg-white/20 px-1.5 text-xs">{{ active }}</span>
      </button>
    </div>
    <div v-if="open" class="card space-y-3 p-3">
      <div class="grid grid-cols-2 gap-2">
        <div><label class="label">From</label><input v-model="f.from_date" type="date" class="input" /></div>
        <div><label class="label">To</label><input v-model="f.to_date" type="date" class="input" /></div>
      </div>
      <div v-if="team.length">
        <label class="label">Sales rep</label>
        <select v-model="f.sales_rep" class="input">
          <option value="">Everyone</option>
          <option v-for="r in team" :key="r.user" :value="r.user">{{ r.name }}</option>
        </select>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-for="o in statusOptions" :key="o.label" type="button" class="chip" :class="{ 'chip-on': f[o.key] === o.value }" @click="toggleStatus(o)">{{ o.label }}</button>
        <button v-if="active" type="button" class="ml-auto text-sm text-brand-700" @click="clear">Clear</button>
      </div>
    </div>
  </div>
</template>
