<script setup>
import { ref, computed, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials, outcomeBadge, levelBadge } from "../ui"
import { usePaged } from "../paged"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const isHospital = computed(() => route.name === "hospital")
const p = ref(null)
const error = ref("")
const tab = ref("visits")
const key = () => (isHospital.value ? { hospital: route.params.name } : { doctor: route.params.name })
const visits = usePaged("kayanick_crm.mobile.get_visits", key)
const cases = usePaged("kayanick_crm.case_api.get_cases", key)

async function load() {
  if (!["hospital", "doctor"].includes(route.name)) return  // leaving the page
  p.value = null
  error.value = ""
  try {
    p.value = await call("kayanick_crm.mobile.get_profile", {
      doctype: isHospital.value ? "KC Hospital" : "KC Doctor", name: route.params.name,
    })
  } catch (e) { error.value = e.message }
  visits.reload()
  cases.reload()
}
watch(() => route.fullPath, load, { immediate: true })

const prefill = computed(() => (isHospital.value ? { hospital: route.params.name } : { doctor: route.params.name }))
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/search")
}
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1 truncate" dir="auto">{{ p ? p.info.title : "" }}</h1>
      </div>
    </header>

    <div class="wrap space-y-4 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <div v-if="!p && !error" class="card h-32 animate-pulse"></div>

      <template v-if="p">
        <div class="card p-4">
          <div class="flex items-center gap-3">
            <span class="avatar h-11 w-11 bg-brand-50 text-brand-700">{{ initials(p.info.title) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold" dir="auto">{{ p.info.title }}</p>
              <p class="truncate text-xs text-gray-500">
                {{ isHospital ? [p.info.area, p.info.hospital_type].filter(Boolean).join(" · ") || "Hospital" : "Doctor" }}
              </p>
            </div>
            <span v-if="!isHospital && p.info.relationship_level" class="badge" :class="levelBadge(p.info.relationship_level)">{{ p.info.relationship_level }}</span>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-2 text-center">
            <div class="rounded-lg bg-gray-50 py-2"><p class="text-xs text-gray-500">Last visit</p><p class="text-sm font-medium">{{ p.info.last_visit ? fmt(p.info.last_visit) : "Never" }}</p></div>
            <div class="rounded-lg bg-gray-50 py-2"><p class="text-xs text-gray-500">Next visit</p><p class="text-sm font-medium">{{ p.info.next_visit ? fmt(p.info.next_visit) : "—" }}</p></div>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-2">
            <router-link :to="{ name: 'visit', query: prefill }" class="btn btn-primary"><Icon name="plus" :size="15" />New visit</router-link>
            <router-link :to="{ name: 'case', query: prefill }" class="btn btn-subtle"><Icon name="plus" :size="15" />New case</router-link>
          </div>
        </div>

        <div class="grid grid-cols-2 rounded-lg bg-gray-100 p-1 text-sm font-medium">
          <button class="rounded-md py-1.5" :class="tab === 'visits' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'visits'">
            Visits <span class="text-gray-400">{{ p.counts.visits }}</span>
          </button>
          <button class="rounded-md py-1.5" :class="tab === 'cases' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="tab = 'cases'">
            Cases <span class="text-gray-400">{{ p.counts.cases }}</span>
          </button>
        </div>

        <template v-if="tab === 'visits'">
          <div v-if="!visits.rows.value.length && !visits.loading.value" class="empty"><Icon name="clipboard" :size="24" /><p>No visits yet</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <router-link v-for="v in visits.rows.value" :key="v.name" :to="{ name: 'visit-detail', params: { name: v.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium" dir="auto">{{ isHospital ? v.doctor_title : v.hospital }}</p>
                <p class="truncate text-xs text-gray-500" dir="auto">{{ [fmt(v.visit_date), v.visit_purpose, v.rep_name].filter(Boolean).join(" · ") }}</p>
              </div>
              <span v-if="v.visit_outcome" class="badge" :class="outcomeBadge(v.visit_outcome)">{{ v.visit_outcome }}</span>
              <Icon name="chevron-right" :size="16" class="text-gray-300" />
            </router-link>
          </div>
          <button v-if="visits.rows.value.length && !visits.done.value" type="button" class="btn btn-subtle w-full" :disabled="visits.loading.value" @click="visits.more">{{ visits.loading.value ? "Loading…" : "Load more" }}</button>
        </template>

        <template v-else>
          <div v-if="!cases.rows.value.length && !cases.loading.value" class="empty"><Icon name="cart" :size="24" /><p>No cases yet</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <router-link v-for="c in cases.rows.value" :key="c.name" :to="{ name: 'case-detail', params: { name: c.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium" dir="auto">{{ isHospital ? c.doctor_title : c.hospital }}</p>
                <p class="truncate text-xs text-gray-500" dir="auto">{{ [fmt(c.case_date), c.products.join(", "), c.rep_name].filter(Boolean).join(" · ") }}</p>
              </div>
              <span class="badge" :class="c.attended ? 'badge-green' : 'badge-amber'">{{ c.attended ? "Attended" : "Planned" }}</span>
              <Icon name="chevron-right" :size="16" class="text-gray-300" />
            </router-link>
          </div>
          <button v-if="cases.rows.value.length && !cases.done.value" type="button" class="btn btn-subtle w-full" :disabled="cases.loading.value" @click="cases.more">{{ cases.loading.value ? "Loading…" : "Load more" }}</button>
        </template>
      </template>
    </div>
  </div>
</template>
