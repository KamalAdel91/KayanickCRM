<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, initials } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const rows = ref([])
const loading = ref(true)
const error = ref("")
const toast = ref(route.query.saved ? "Case " + route.query.saved + " saved" : "")

async function load() {
  loading.value = true
  error.value = ""
  try { rows.value = await call("kayanick_crm.case_api.get_cases") }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
onMounted(() => {
  load()
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
      <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <template v-if="loading && !rows.length">
        <div v-for="i in 3" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty">
        <Icon name="cart" :size="24" /><p>No cases yet</p>
        <router-link to="/case/new" class="btn btn-subtle mt-1">Create the first one</router-link>
      </div>
      <div v-else class="card divide-y divide-gray-100">
        <router-link v-for="c in rows" :key="c.name" :to="{ name: 'case-detail', params: { name: c.name } }" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
          <span class="avatar">{{ initials(c.customer_name) }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium" dir="auto">{{ c.customer_name }}</p>
            <p class="truncate text-xs text-gray-500">{{ [fmt(c.case_date), c.products.join(", "), c.name].filter(Boolean).join(" · ") }}</p>
          </div>
          <span class="badge" :class="c.attended ? 'badge-green' : 'badge-amber'">{{ c.attended ? "Attended" : "Planned" }}</span>
          <Icon name="chevron-right" :size="16" class="text-gray-300" />
        </router-link>
      </div>
    </div>
  </div>
</template>
