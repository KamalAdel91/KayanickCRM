<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, fmtTime, usedItemsError, localToday } from "../ui"
import Icon from "../components/Icon.vue"
import RecordNav from "../components/RecordNav.vue"
import FileList from "../components/FileList.vue"
import UsedItems from "../components/UsedItems.vue"
import AttendeePick from "../components/AttendeePick.vue"

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
const ans = ref({ used: "", items: [], by: null })
function startAttend() {
  error.value = ""
  ans.value = { used: "", items: [], by: null }
  postponing.value = false
  cancelling.value = false
  answering.value = true
}
// cancel: reason is required; the case stays for history and can be reopened
const cancelling = ref(false)
const cancelReason = ref("")
function startCancel() {
  error.value = ""
  cancelReason.value = ""
  answering.value = false
  postponing.value = false
  cancelling.value = true
}
async function submitCancel() {
  error.value = ""
  if (!cancelReason.value.trim()) { error.value = "Write why the case is cancelled"; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  marking.value = true
  try {
    await call("kayanick_crm.case_api.cancel_case", { name: c.value.name, reason: cancelReason.value }, { post: true })
    cancelling.value = false
    await load()
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
  finally { marking.value = false }
}
async function reopen() {
  if (!window.confirm("Reopen this case as planned?")) return
  error.value = ""
  marking.value = true
  try {
    await call("kayanick_crm.case_api.reopen_case", { name: c.value.name }, { post: true })
    await load()
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
  finally { marking.value = false }
}
// postpone: new date + time, optional reason; the old date/time is kept in the log
const postponing = ref(false)
const pp = ref({ date: "", time: "", reason: "" })
const hhmm = (t) => {
  const [h, m] = String(t || "").split(":")
  return h ? h.padStart(2, "0") + ":" + (m || "00").padStart(2, "0") : ""
}
function startPostpone() {
  error.value = ""
  pp.value = { date: c.value.case_date < localToday() ? localToday() : c.value.case_date, time: hhmm(c.value.case_time), reason: "" }
  answering.value = false
  cancelling.value = false
  postponing.value = true
}
async function submitPostpone() {
  error.value = ""
  const err = !pp.value.date || !pp.value.time ? "Choose the new date and time"
    : pp.value.date < localToday() ? "The new date can't be in the past" : ""
  if (err) { error.value = err; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  marking.value = true
  try {
    await call("kayanick_crm.case_api.postpone_case", {
      name: c.value.name, case_date: pp.value.date, case_time: pp.value.time, reason: pp.value.reason,
    }, { post: true })
    postponing.value = false
    await load()
  } catch (e) { error.value = e.message; window.scrollTo({ top: 0, behavior: "smooth" }) }
  finally { marking.value = false }
}
async function submitAttended(attended) {
  error.value = ""
  if (attended) {
    const err = usedItemsError(ans.value.used, ans.value.items)
    if (err) { error.value = err; window.scrollTo({ top: 0, behavior: "smooth" }); return }
  }
  marking.value = true
  try {
    const r = await call("kayanick_crm.case_api.set_attended", {
      name: c.value.name, attended: attended ? 1 : 0, used_products: attended ? ans.value.used : "",
      attended_by: attended && ans.value.by ? ans.value.by.name : "",
      used_items: attended && ans.value.used === "Yes" ? ans.value.items.map((r) => ({ item_code: r.item_code, qty: r.qty })) : [],
    }, { post: true })
    answering.value = false
    // attended by someone outside this user's records: the case is his now
    if (r && r.can_read === false) { router.replace({ name: "cases", query: { tab: "attended" } }); return }
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
      <RecordNav kind="cases" route="case-detail" />
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
            <span class="badge" :class="c.cancelled ? 'badge-red' : c.attended ? 'badge-green' : 'badge-amber'">{{ c.cancelled ? "Cancelled" : c.attended ? "Attended" : "Planned" }}</span>
          </div>
          <div v-if="c.postponements.length" class="flex items-center gap-1 px-4 py-2 text-xs text-amber-700">
            <Icon name="calendar" :size="12" />Postponed {{ c.postponements.length }} time{{ c.postponements.length === 1 ? "" : "s" }}
          </div>
          <div v-if="c.cancelled" class="px-4 py-3">
            <p class="text-xs text-gray-500">Cancelled{{ c.cancelled_by_name ? " by " + c.cancelled_by_name : "" }}</p>
            <p class="whitespace-pre-line text-sm text-red-700" dir="auto">{{ c.cancel_reason }}</p>
          </div>
          <div v-if="c.attended && c.attended_by_name" class="px-4 py-3">
            <p class="text-xs text-gray-500">Attended by</p><p dir="auto">{{ c.attended_by_name }}</p>
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
                <span class="block break-words text-sm font-medium" dir="auto">{{ r.item_name }}</span>
                <span v-if="r.item_code !== r.item_name" class="block break-words text-xs text-gray-500">{{ r.item_code }}</span>
              </span>
              <span class="shrink-0 text-sm font-medium">{{ r.qty }}<span v-if="r.uom" class="text-xs text-gray-500"> {{ r.uom }}</span></span>
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

        <section v-if="c.postponements.length">
          <p class="section-label"><Icon name="calendar" :size="14" />Postponement log · {{ c.postponements.length }}</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="(r, i) in [...c.postponements].reverse()" :key="i" class="px-4 py-2.5 text-sm">
              <p>
                <span class="text-gray-500 line-through">{{ fmt(r.from_date) }}<span v-if="r.from_time"> · {{ fmtTime(r.from_time) }}</span></span>
                → <span class="font-medium">{{ fmt(r.to_date) }}<span v-if="r.to_time"> · {{ fmtTime(r.to_time) }}</span></span>
              </p>
              <p v-if="r.reason" class="whitespace-pre-line text-gray-700" dir="auto">{{ r.reason }}</p>
              <p class="text-xs text-gray-400" dir="auto">{{ r.by }}</p>
            </div>
          </div>
        </section>

        <section v-if="answering">
          <p class="section-label"><Icon name="cart" :size="14" />Mark as attended</p>
          <div class="card space-y-3 p-4">
            <AttendeePick v-model="ans.by" />
            <UsedItems v-model:used="ans.used" v-model:items="ans.items" />
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button type="button" class="btn btn-subtle h-11" :disabled="marking" @click="answering = false">Cancel</button>
              <button type="button" class="btn btn-primary h-11" :disabled="marking" @click="submitAttended(true)">{{ marking ? "Saving…" : "Save" }}</button>
            </div>
          </div>
        </section>
        <section v-else-if="postponing">
          <p class="section-label"><Icon name="calendar" :size="14" />Postpone case</p>
          <div class="card space-y-3 p-4">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">New date<span class="text-red-500"> *</span></label>
                <input v-model="pp.date" type="date" class="input" :min="localToday()" />
              </div>
              <div>
                <label class="label">New time<span class="text-red-500"> *</span></label>
                <input v-model="pp.time" type="time" class="input" />
              </div>
            </div>
            <div>
              <label class="label">Reason</label>
              <textarea v-model="pp.reason" rows="2" placeholder="Why is it postponed? (optional)" class="input h-auto resize-none py-2" dir="auto"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button type="button" class="btn btn-subtle h-11" :disabled="marking" @click="postponing = false">Cancel</button>
              <button type="button" class="btn btn-primary h-11" :disabled="marking" @click="submitPostpone">{{ marking ? "Saving…" : "Postpone" }}</button>
            </div>
          </div>
        </section>
        <section v-else-if="cancelling">
          <p class="section-label"><Icon name="x" :size="14" />Cancel case</p>
          <div class="card space-y-3 p-4">
            <div>
              <label class="label">Reason<span class="text-red-500"> *</span></label>
              <textarea v-model="cancelReason" rows="2" placeholder="Why is the case cancelled?" class="input h-auto resize-none py-2" dir="auto"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button type="button" class="btn btn-subtle h-11" :disabled="marking" @click="cancelling = false">Back</button>
              <button type="button" class="btn h-11 border border-red-200 bg-red-600 text-white" :disabled="marking" @click="submitCancel">{{ marking ? "Saving…" : "Cancel case" }}</button>
            </div>
          </div>
        </section>
        <template v-else-if="c.can_edit">
          <button v-if="c.cancelled" type="button" class="btn btn-subtle h-11 w-full" :disabled="marking" @click="reopen">
            <Icon name="refresh" :size="16" />Reopen case
          </button>
          <button v-else-if="c.attended" type="button" class="btn btn-subtle h-11 w-full" :disabled="marking" @click="submitAttended(false)">
            <Icon name="calendar" :size="16" />Mark as planned
          </button>
          <template v-else>
            <button type="button" class="btn btn-primary h-11 w-full" @click="startAttend">
              <Icon name="check" :size="16" />Mark as attended
            </button>
            <div v-if="c.can_postpone" class="grid grid-cols-2 gap-2">
              <button type="button" class="btn btn-subtle h-11" @click="startPostpone">
                <Icon name="calendar" :size="16" />Postpone
              </button>
              <button type="button" class="btn h-11 border border-red-200 bg-red-50 text-red-700" @click="startCancel">
                <Icon name="x" :size="16" />Cancel case
              </button>
            </div>
          </template>
        </template>
        <button v-if="c.can_delete" type="button" class="btn h-11 w-full border border-red-200 bg-red-50 text-red-700" :disabled="deleting" @click="remove">
          {{ deleting ? "Deleting…" : "Delete case" }}
        </button>
      </template>
    </div>
  </div>
</template>
