<script setup>
import { ref, onMounted } from "vue"
import { call } from "../api"
import { fmt, initials, outcomeBadge } from "../ui"
import Icon from "../components/Icon.vue"

const rows = ref([])
const loading = ref(true)
const error = ref("")
onMounted(async () => {
  try { rows.value = await call("kayanick_crm.mobile.get_visits") }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Visits</h1>
        <router-link to="/visit" class="btn btn-primary"><Icon name="plus" :size="15" />New visit</router-link>
      </div>
    </header>
    <div class="wrap space-y-3 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <template v-if="loading">
        <div v-for="i in 4" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty">
        <Icon name="clipboard" :size="24" /><p>No visits yet</p>
        <router-link to="/visit" class="btn btn-subtle mt-1">Log the first one</router-link>
      </div>
      <div v-else class="card divide-y divide-gray-100">
        <router-link v-for="v in rows" :key="v.name" :to="{ name: 'visit-detail', params: { name: v.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
          <span class="avatar">{{ initials(v.hospital) }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium" dir="auto">{{ v.hospital }}</p>
            <p class="truncate text-xs text-gray-500" dir="auto">{{ [fmt(v.visit_date), v.doctor_title, v.rep_name].filter(Boolean).join(" · ") }}</p>
          </div>
          <span v-if="v.visit_outcome" class="badge" :class="outcomeBadge(v.visit_outcome)">{{ v.visit_outcome }}</span>
          <Icon name="chevron-right" :size="16" class="text-gray-300" />
        </router-link>
      </div>
    </div>
  </div>
</template>
