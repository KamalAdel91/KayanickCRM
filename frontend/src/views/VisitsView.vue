<script setup>
import { reactive, watch, onMounted } from "vue"
import { fmt, initials, outcomeBadge } from "../ui"
import { usePaged } from "../paged"
import Icon from "../components/Icon.vue"
import FilterBar from "../components/FilterBar.vue"

const f = reactive({ text: "", from_date: "", to_date: "", sales_rep: "", outcome: "" })
const { rows, loading, done, error, reload, more } = usePaged("kayanick_crm.mobile.get_visits", () => ({ ...f }))
let timer = null
watch(f, () => { clearTimeout(timer); timer = setTimeout(reload, 300) })
onMounted(reload)
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
      <FilterBar v-model="f" kind="visits" />
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <template v-if="loading && !rows.length">
        <div v-for="i in 4" :key="i" class="card h-16 animate-pulse"></div>
      </template>
      <div v-else-if="!rows.length" class="empty">
        <Icon name="clipboard" :size="24" /><p>No visits found</p>
      </div>
      <template v-else>
        <div class="card divide-y divide-gray-100">
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
        <button v-if="!done" type="button" class="btn btn-subtle w-full" :disabled="loading" @click="more">{{ loading ? "Loading…" : "Load more" }}</button>
        <p v-else class="py-1 text-center text-xs text-gray-400">{{ rows.length }} visit{{ rows.length === 1 ? "" : "s" }}</p>
      </template>
    </div>
  </div>
</template>
