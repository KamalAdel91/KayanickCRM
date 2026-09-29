<script setup>
import { ref, watch, onMounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import Icon from "../components/Icon.vue"

const router = useRouter()
const q = ref("")
const tab = ref("accounts")
const res = ref({ accounts: [], doctors: [] })
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
function initials(s) {
  return (s || "?").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase()
}
function logVisit(hospital, title) {
  router.push({ name: "visit", query: { hospital, title } })
}
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner"><h1 class="page-title">Search</h1></div>
    </header>

    <div class="wrap space-y-3 py-3">
      <div class="relative">
        <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon name="search" :size="16" /></span>
        <input v-model="q" type="search" placeholder="Search hospitals, doctors, cities" class="input pl-9 pr-9" dir="auto" />
        <button v-if="q" class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400" @click="q = ''"><Icon name="x" :size="16" /></button>
      </div>

      <div class="grid grid-cols-2 rounded-lg bg-gray-100 p-1 text-sm font-medium">
        <button class="rounded-md py-1.5" :class="tab === 'accounts' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'accounts'">
          Hospitals <span class="text-gray-400">{{ res.accounts.length }}</span>
        </button>
        <button class="rounded-md py-1.5" :class="tab === 'doctors' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'doctors'">
          Doctors <span class="text-gray-400">{{ res.doctors.length }}</span>
        </button>
      </div>

      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <template v-if="tab === 'accounts'">
        <div v-if="!res.accounts.length && !loading" class="empty"><Icon name="building" :size="24" /><p>No hospitals found</p></div>
        <div v-else class="card divide-y divide-gray-100">
          <button v-for="a in res.accounts" :key="a.name" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-gray-50"
            @click="logVisit(a.name, a.account_name)">
            <span class="avatar">{{ initials(a.account_name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ a.account_name }}</span>
              <span class="block truncate text-xs text-gray-500">
                {{ [a.city, a.tier ? "Tier " + a.tier : ""].filter(Boolean).join(" · ") }} · last visit {{ a.last_visit || "never" }}
              </span>
            </span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </button>
        </div>
      </template>

      <template v-else>
        <div v-if="!res.doctors.length && !loading" class="empty"><Icon name="user" :size="24" /><p>No doctors found</p></div>
        <div v-else class="card divide-y divide-gray-100">
          <button v-for="d in res.doctors" :key="d.name" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-gray-50"
            @click="logVisit(d.hospital_account, d.hospital_title)">
            <span class="avatar">{{ initials(d.doctor_name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium" dir="auto">{{ d.doctor_name }}</span>
              <span class="block truncate text-xs text-gray-500" dir="auto">{{ [d.specialty, d.hospital_title].filter(Boolean).join(" · ") }}</span>
            </span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
