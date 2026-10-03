<script setup>
import { ref, watch, onMounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials, levelBadge } from "../ui"
import Icon from "../components/Icon.vue"
import AddSheet from "../components/AddSheet.vue"
import { getOptions } from "../options"

const router = useRouter()
const q = ref("")
const tab = ref("hospitals")
const res = ref({ hospitals: [], doctors: [] })
const error = ref("")
const loading = ref(false)
let timer = null

async function run() {
  error.value = ""
  loading.value = true
  try { res.value = await call("kayanick_crm.mobile.search", { text: q.value }) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
watch(q, () => { clearTimeout(timer); timer = setTimeout(run, 300) })
onMounted(run)

const opts = ref({})
onMounted(async () => { try { opts.value = await getOptions() } catch (e) {} })
const adding = ref(false)
const canAdd = () => (tab.value === "hospitals" ? opts.value.can_add_hospital : opts.value.can_add_doctor)
function added(r) {
  if (tab.value === "hospitals") router.push({ name: "hospital", params: { name: r.name } })
  else router.push({ name: "doctor", params: { name: r.name } })
}

</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Search</h1>
        <button v-if="canAdd()" type="button" class="btn btn-primary" @click="adding = true">
          <Icon name="plus" :size="16" />{{ tab === "hospitals" ? "Hospital" : "Doctor" }}
        </button>
      </div>
    </header>

    <div class="wrap space-y-3 py-3">
      <div class="relative">
        <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
        <input v-model="q" type="search" placeholder="Search hospitals, doctors, areas" class="input pl-9 pr-9" dir="auto" />
        <button v-if="q" class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400" @click="q = ''"><Icon name="x" :size="16" /></button>
      </div>

      <div class="grid grid-cols-2 rounded-lg bg-gray-100 p-1 text-sm font-medium">
        <button class="rounded-md py-1.5" :class="tab === 'hospitals' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'hospitals'">
          Hospitals <span class="text-gray-400">{{ res.hospitals.length }}</span>
        </button>
        <button class="rounded-md py-1.5" :class="tab === 'doctors' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'doctors'">
          Doctors <span class="text-gray-400">{{ res.doctors.length }}</span>
        </button>
      </div>

      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <template v-if="tab === 'hospitals'">
        <div v-if="!res.hospitals.length && !loading" class="empty"><Icon name="building" :size="24" /><p>No hospitals found</p></div>
        <div v-else class="card divide-y divide-gray-100">
          <button v-for="h in res.hospitals" :key="h.name" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-gray-50" @click="router.push({ name: 'hospital', params: { name: h.name } })">
            <span class="avatar">{{ initials(h.name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ h.name }}</span>
              <span class="block truncate text-xs text-gray-500">
                {{ [h.area, h.hospital_type, "last visit " + (h.last_visit ? fmt(h.last_visit) : "never")].filter(Boolean).join(" · ") }}
              </span>
            </span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </button>
        </div>
      </template>

      <template v-else>
        <div v-if="!res.doctors.length && !loading" class="empty"><Icon name="user" :size="24" /><p>No doctors found</p></div>
        <div v-else class="card divide-y divide-gray-100">
          <button v-for="d in res.doctors" :key="d.name" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-gray-50" @click="router.push({ name: 'doctor', params: { name: d.name } })">
            <span class="avatar">{{ initials(d.doctor_name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ d.doctor_name }}</span>
              <span class="block truncate text-xs text-gray-500">{{ "last visit " + (d.last_visit ? fmt(d.last_visit) : "never") }}</span>
            </span>
            <span v-if="d.relationship_level" class="badge" :class="levelBadge(d.relationship_level)">{{ d.relationship_level }}</span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </button>
        </div>
      </template>
    </div>
    <AddSheet v-model:open="adding" :kind="tab === 'hospitals' ? 'hospital' : 'doctor'" :initial="q" :options="opts" @added="added" />
  </div>
</template>
