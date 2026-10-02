<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, fmtTime, usedItemsError } from "../ui"
import Icon from "../components/Icon.vue"
import FileList from "../components/FileList.vue"
import UsedItems from "../components/UsedItems.vue"

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
// marking attended asks "used products?" first
const answering = ref(false)
const ans = ref({ used: "", items: [] })
function startAttend() {
  error.value = ""
  ans.value = { used: "", items: [] }
  answering.value = true
}
async function submitAttended(attended) {
  error.value = ""
  if (attended) {
    const err = usedItemsError(ans.value.used, ans.value.items)
    if (err) { error.value = err; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  }
  marking.value = true
  try {
    await call("kayanick_crm.case_api.set_attended", {
      name: c.value.name, attended: attended ? 1 : 0, used_products: attended ? ans.value.used : "",
      used_items: attended && ans.value.used === "Yes" ? ans.value.items.map((r) => ({ item_code: r.item_code, qty: r.qty })) : [],
    }, { post: true })
    answering.value = false
    await load()
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
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
            <p class="font-medium" dir="auto">{{ c.hospital }}</p>
            <p class="text-sm text-gray-500" dir="auto">{{ c.doctor_title }}</p>
            <p class="mt-0.5 flex items-center gap-1 text-xs text-gray-500"><Icon name="user" :size="12" />{{ c.rep_name }}</p>
          </div>
          <div class="flex items-center px-4 py-3">
            <div class="flex-1"><p class="text-xs text-gray-500">Case date</p><p>{{ fmt(c.case_date) }}<span v-if="c.case_time" class="text-gray-500"> · {{ fmtTime(c.case_time) }}</span></p></div>
            <span class="badge" :class="c.attended ? 'badge-green' : 'badge-amber'">{{ c.attended ? "Attended" : "Planned" }}</span>
          </div>
        </div>

        <section v-if="c.products.length">
          <p class="section-label"><Icon name="clipboard" :size="14" />Products</p>
          <div class="card flex flex-wrap gap-2 p-4">
            <span v-for="p in c.products" :key="p" class="badge badge-blue">{{ p }}</span>
          </div>
        </section>

        <section v-if="c.attended && c.used_products">
          <p class="section-label"><Icon name="cart" :size="14" />Used products · {{ c.used_products }}</p>
          <div v-if="c.used_items.length" class="card divide-y divide-gray-100">
            <div v-for="r in c.used_items" :key="r.item_code" class="flex items-center gap-3 px-4 py-2.5">
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium" dir="auto">{{ r.item_name }}</span>
                <span class="block truncate text-xs text-gray-500">{{ r.item_code }}</span>
              </span>
              <span class="text-sm font-medium">{{ r.qty }}<span v-if="r.uom" class="text-xs text-gray-500"> {{ r.uom }}</span></span>
            </div>
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

        <section v-if="answering">
          <p class="section-label"><Icon name="cart" :size="14" />Mark as attended</p>
          <div class="card space-y-3 p-4">
            <UsedItems v-model:used="ans.used" v-model:items="ans.items" />
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button type="button" class="btn btn-subtle h-11" :disabled="marking" @click="answering = false">Cancel</button>
              <button type="button" class="btn btn-primary h-11" :disabled="marking" @click="submitAttended(true)">{{ marking ? "Saving…" : "Save" }}</button>
            </div>
          </div>
        </section>
        <template v-else-if="c.can_edit">
          <button v-if="c.attended" type="button" class="btn btn-subtle h-11 w-full" :disabled="marking" @click="submitAttended(false)">
            <Icon name="calendar" :size="16" />Mark as planned
          </button>
          <button v-else type="button" class="btn btn-primary h-11 w-full" @click="startAttend">
            <Icon name="check" :size="16" />Mark as attended
          </button>
        </template>
        <button v-if="c.can_delete" type="button" class="btn h-11 w-full border border-red-200 bg-red-50 text-red-700" :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Delete case" }}
        </button>
      </template>
    </div>
  </div>
</template>
