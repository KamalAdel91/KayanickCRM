<script setup>
import { ref, reactive, watch, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { fmt, initials, fmtTime } from "../ui"
import { usePaged } from "../paged"
import Icon from "../components/Icon.vue"
import FilterBar from "../components/FilterBar.vue"

const route = useRoute()
const router = useRouter()
const f = reactive({ text: "", from_date: "", to_date: "", sales_rep: "", attended: route.query.tab === "attended" ? 1 : route.query.tab === "all" ? "" : 0 })
const tabs = [{ label: "Planned", value: 0 }, { label: "Attended", value: 1 }, { label: "All", value: "" }]
const { rows, loading, done, error, reload, more } = usePaged("kayanick_crm.case_api.get_cases", () => ({ ...f }))
let timer = null
watch(f, () => { clearTimeout(timer); timer = setTimeout(reload, 300) })
const toast = ref(route.query.saved ? "Case " + route.query.saved + " saved" : "")

onMounted(() => {
  reload()
  if (toast.value) {
    router.replace({ query: {} })
    setTimeout(() => (toast.value = ""), 3500)
  }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Cases</h1>
        <router-link to="/case/new" class="btn btn-primary"><Icon name="plus" :size="15" />New case</router-link>
      </div>
    </header>

    <div class="wrap space-y-3 py-4">
      <div class="grid grid-cols-3 rounded-lg bg-gray-100 p-1 text-sm font-medium">
        <button v-for="t in tabs" :key="t.label" type="button" class="rounded-md py-1.5"
          :class="f.attended === t.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'" @click="f.attended = t.value">{{ t.label }}</button>
      </div>
      <FilterBar v-model="f" kind="cases" />
      <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <template v-if="loading && !rows.length">
        <div v-for="i in 3" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty">
        <Icon name="cart" :size="24" /><p>{{ f.attended === 0 ? "No planned cases" : f.attended === 1 ? "No attended cases" : "No cases found" }}</p>
      </div>
      <template v-else>
      <div class="card divide-y divide-gray-100">
        <router-link v-for="c in rows" :key="c.name" :to="{ name: 'case-detail', params: { name: c.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
          <span class="avatar">{{ initials(c.hospital) }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium" dir="auto">{{ c.hospital }}</p>
            <p class="truncate text-xs text-gray-500">{{ [fmt(c.case_date) + (c.case_time ? ' · ' + fmtTime(c.case_time) : ''), c.doctor_title, c.attended ? c.attended_by_name || c.rep_name : c.rep_name].filter(Boolean).join(" · ") }}</p>
          </div>
          <span class="badge" :class="c.attended ? 'badge-green' : 'badge-amber'">{{ c.attended ? "Attended" : "Planned" }}</span>
          <Icon name="chevron-right" :size="16" class="text-gray-300" />
        </router-link>
      </div>
      <button v-if="!done" type="button" class="btn btn-subtle w-full" :disabled="loading" @click="more">{{ loading ? "Loading…" : "Load more" }}</button>
      <p v-else class="py-1 text-center text-xs text-gray-400">{{ rows.length }} case{{ rows.length === 1 ? "" : "s" }}</p>
      </template>
    </div>
  </div>
</template>
