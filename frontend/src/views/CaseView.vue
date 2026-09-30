<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt } from "../ui"
import Icon from "../components/Icon.vue"
import FileList from "../components/FileList.vue"

const route = useRoute()
const router = useRouter()
const c = ref(null)
const error = ref("")

async function load() {
  try { c.value = await call("kayanick_crm.case_api.get_case", { name: route.params.name }) }
  catch (e) { error.value = e.message }
}
const deleting = ref(false)
const marking = ref(false)
async function toggleAttended() {
  marking.value = true
  error.value = ""
  try {
    c.value.attended = await call("kayanick_crm.case_api.set_attended", { name: c.value.name, attended: c.value.attended ? 0 : 1 }, { post: true })
  } catch (e) { error.value = e.message }
  finally { marking.value = false }
}
async function remove() {
  if (!window.confirm(`Delete ${route.params.name}? This can't be undone.`)) return
  deleting.value = true
  error.value = ""
  try {
    await call("kayanick_crm.mobile.delete_record", { doctype: "KC Case", name: route.params.name }, { post: true })
    router.replace("/cases")
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
  finally { deleting.value = false }
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/cases")
}
onMounted(load)
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
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <div v-if="!c && !error" class="card h-40 animate-pulse"></div>

      <template v-if="c">
        <div class="card divide-y divide-gray-100">
          <div class="px-4 py-3">
            <p class="text-xs text-gray-500">Customer</p>
            <p class="font-medium" dir="auto">{{ c.customer_name }}</p>
            <p class="mt-0.5 flex items-center gap-1 text-xs text-gray-500"><Icon name="user" :size="12" />{{ c.rep_name }}</p>
          </div>
          <div class="flex items-center px-4 py-3">
            <div class="flex-1"><p class="text-xs text-gray-500">Case date</p><p>{{ fmt(c.case_date) }}</p></div>
            <span class="badge" :class="c.attended ? 'badge-green' : 'badge-amber'">{{ c.attended ? "Attended" : "Planned" }}</span>
          </div>
        </div>

        <section v-if="c.products.length">
          <p class="section-label"><Icon name="clipboard" :size="14" />Products</p>
          <div class="card flex flex-wrap gap-2 p-4">
            <span v-for="p in c.products" :key="p" class="badge badge-blue">{{ p }}</span>
          </div>
        </section>

        <section v-if="c.notes">
          <p class="section-label"><Icon name="file-text" :size="14" />Notes</p>
          <div class="card whitespace-pre-line p-4 text-sm" dir="auto">{{ c.notes }}</div>
        </section>

        <section>
          <p class="section-label"><Icon name="paperclip" :size="14" />Attachments · {{ c.attachments.length }}</p>
          <div class="card p-4"><FileList :files="c.attachments" /></div>
        </section>

        <button v-if="c.can_edit" type="button" class="btn h-11 w-full" :class="c.attended ? 'btn-subtle' : 'btn-primary'" :disabled="marking" @click="toggleAttended">
          <Icon :name="c.attended ? 'calendar' : 'check'" :size="16" />{{ c.attended ? "Mark as planned" : "Mark as attended" }}
        </button>
        <button v-if="c.can_delete" type="button" class="btn h-11 w-full border border-red-200 bg-red-50 text-red-700" :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Delete case" }}
        </button>
      </template>
    </div>
  </div>
</template>
