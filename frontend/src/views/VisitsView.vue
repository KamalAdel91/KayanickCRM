<script setup>
import { reactive, watch, onActivated } from "vue"
import { useRoute, useRouter } from "vue-router"
import { fmt, initials, outcomeBadge, ymd } from "../ui"
import { usePaged } from "../paged"
import Icon from "../components/Icon.vue"
import FilterBar from "../components/FilterBar.vue"
import { registerList } from "../listnav"

defineOptions({ name: "VisitsView" })
const route = useRoute()
const router = useRouter()

const f = reactive({ text: "", from_date: "", to_date: "", sales_rep: "", outcome: "", order_expected: "", due: "" })
const paged = usePaged("kayanick_crm.mobile.get_visits", () => ({ ...f }))
const { rows, loading, done, error, reload, more } = paged
registerList("visits", paged)
let timer = null
watch(f, () => { clearTimeout(timer); timer = setTimeout(reload, 300) })
let first = true

// opened from a card on Today: ?period=month, ?order=1 (orders expected), ?due=1 (follow-ups due)
function preset(q) {
  if (!q.period && !q.order && !q.due) return null
  const d = new Date()
  const month = q.period === "month"
  return { text: "", sales_rep: "", outcome: "",
    from_date: month ? ymd(new Date(d.getFullYear(), d.getMonth(), 1)) : "",
    to_date: month ? ymd(new Date(d.getFullYear(), d.getMonth() + 1, 0)) : "",
    order_expected: q.order ? 1 : "", due: q.due ? 1 : "" }
}
// the page is kept alive: first visit loads, coming back refreshes in place (same filters and scroll)
onActivated(() => {
  let changed = false
  const want = preset(route.query)
  if (want) {
    changed = Object.keys(want).some((k) => f[k] !== want[k])
    Object.assign(f, want)
    router.replace({ query: {} })
  }
  if (changed) first = false  // the filter watcher reloads
  else if (first) { first = false; reload() }
  else paged.refresh()
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
