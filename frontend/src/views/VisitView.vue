<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, outcomeBadge, levelBadge } from "../ui"
import Icon from "../components/Icon.vue"
import RecordNav from "../components/RecordNav.vue"
import FileList from "../components/FileList.vue"

const route = useRoute()
const router = useRouter()
const v = ref(null)
const error = ref("")

const deleting = ref(false)
async function remove() {
  if (!window.confirm(`Delete ${route.params.name}? This can't be undone.`)) return
  deleting.value = true
  error.value = ""
  try {
    await call("kayanick_crm.mobile.delete_record", { doctype: "KC Visit", name: route.params.name }, { post: true })
    router.replace("/visits")
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
  finally { deleting.value = false }
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/visits")
}
onMounted(async () => {
  try { v.value = await call("kayanick_crm.mobile.get_visit", { name: route.params.name }) }
  catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1 truncate">{{ route.params.name }}</h1>
      </div>
    </header>

    <div class="wrap space-y-5 py-4">
      <RecordNav kind="visits" route="visit-detail" />
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <div v-if="!v && !error" class="card h-40 animate-pulse"></div>

      <template v-if="v">
        <div class="card divide-y divide-gray-100">
          <div class="px-4 py-3">
            <p class="font-medium" dir="auto">{{ v.hospital }}</p>
            <p class="text-sm text-gray-500" dir="auto">{{ v.doctor_title }}</p>
            <p class="mt-0.5 flex items-center gap-1 text-xs text-gray-500"><Icon name="user" :size="12" />{{ v.sales_rep }}</p>
          </div>
          <div class="flex px-4 py-3">
            <div class="flex-1"><p class="text-xs text-gray-500">Date</p><p>{{ fmt(v.visit_date) }}</p></div>
            <div class="flex-1"><p class="text-xs text-gray-500">Purpose</p><p>{{ v.visit_purpose || "—" }}</p></div>
          </div>
          <div v-if="v.doctors.length" class="space-y-1.5 px-4 py-3">
            <p class="text-xs text-gray-500">Relationship</p>
            <div v-for="d in v.doctors" :key="d.doctor" class="flex items-center justify-between gap-2 text-sm">
              <span class="min-w-0 truncate" dir="auto">{{ d.doctor_name }}</span>
              <span v-if="d.relationship_level" class="badge shrink-0" :class="levelBadge(d.relationship_level)">{{ d.relationship_level }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2 px-4 py-3">
            <span v-if="v.visit_outcome" class="badge" :class="outcomeBadge(v.visit_outcome)">{{ v.visit_outcome }}</span>
            <span v-if="v.order_expected" class="badge badge-blue"><Icon name="cart" :size="11" />Order expected</span>
            <span v-for="p in v.products" :key="p" class="badge badge-gray">{{ p }}</span>
          </div>
        </div>

        <section v-if="v.notes">
          <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
          <div class="card whitespace-pre-line p-4 text-sm" dir="auto">{{ v.notes }}</div>
        </section>

        <section v-if="v.next_action || v.next_visit_date">
          <p class="section-label"><Icon name="flag" :size="14" />Next step</p>
          <div class="card p-4 text-sm">
            <p v-if="v.next_action" class="whitespace-pre-line" dir="auto">{{ v.next_action }}</p>
            <p v-if="v.next_visit_date" class="mt-1 flex items-center gap-1 text-xs text-gray-500"><Icon name="calendar" :size="12" />{{ fmt(v.next_visit_date) }}</p>
          </div>
        </section>

        <section>
          <p class="section-label"><Icon name="paperclip" :size="14" />Attachments · {{ v.attachments.length }}</p>
          <div class="card p-4"><FileList :files="v.attachments" /></div>
        </section>

        <button v-if="v.can_delete" type="button" class="btn h-11 w-full border border-red-200 bg-red-50 text-red-700" :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Delete visit" }}
        </button>
      </template>
    </div>
  </div>
</template>
