<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, money } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const inv = ref(null)
const error = ref("")
const busy = ref(false)

// invoices go back past this year: show the year when it isn't this one
function day(v) {
  if (!v) return ""
  const y = String(v).slice(0, 4)
  return fmt(v) + (y === String(new Date().getFullYear()) ? "" : " " + y)
}
function qty(n) {
  return Number(n).toLocaleString("en-US", { maximumFractionDigits: 3 })
}
function back() {
  if (window.history.length > 1) router.back()
  else router.push("/debts")
}

// the printed invoice: shared as a file where the phone can (WhatsApp etc.), otherwise opened
async function pdf() {
  busy.value = true
  error.value = ""
  try {
    const res = await fetch("/api/method/kayanick_crm.debt_api.invoice_pdf?name=" + encodeURIComponent(inv.value.name),
      { credentials: "same-origin" })
    if (!res.ok || !(res.headers.get("Content-Type") || "").includes("pdf")) throw new Error("Couldn't create the PDF, ask the admin to check invoice printing")
    const file = new File([await res.blob()], inv.value.name + ".pdf", { type: "application/pdf" })
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], title: inv.value.name }) } catch (e) {}
    } else {
      window.open(URL.createObjectURL(file), "_blank")
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  try { inv.value = await call("kayanick_crm.debt_api.get_invoice", { name: route.params.name }) }
  catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1 truncate">{{ route.params.name }}</h1>
        <button v-if="inv" type="button" class="btn btn-subtle" :disabled="busy" @click="pdf"><Icon name="file-text" :size="15" />{{ busy ? "…" : "PDF" }}</button>
      </div>
    </header>

    <div class="wrap space-y-4 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <template v-if="!inv && !error">
        <div v-for="i in 3" :key="i" class="card h-20 animate-pulse"></div>
      </template>

      <template v-if="inv">
        <div class="card p-4">
          <div class="flex items-start gap-2">
            <p class="min-w-0 flex-1 font-semibold" dir="auto">{{ inv.customer_name }}</p>
            <span v-if="inv.is_return" class="badge badge-gray">Credit note</span>
            <span v-else-if="inv.days_overdue" class="badge" :class="inv.days_overdue > 90 ? 'badge-red' : 'badge-amber'">{{ inv.days_overdue }}d overdue</span>
            <span v-else-if="inv.outstanding > 0" class="badge badge-blue">Not due</span>
            <span v-else class="badge badge-green">Paid</span>
          </div>
          <p class="mt-1 text-xs text-gray-500">{{ day(inv.posting_date) }} · due {{ day(inv.due_date) }}<template v-if="inv.po_no"> · PO {{ inv.po_no }}</template></p>
          <p v-if="inv.subject" class="mt-2 text-sm" dir="auto">{{ inv.subject }}</p>
          <div class="mt-3 grid grid-cols-3 gap-2 text-sm">
            <div class="rounded-lg bg-gray-50 px-3 py-2">
              <p class="text-xs text-gray-500">Total</p>
              <p class="font-semibold">{{ money(inv.grand_total) }}</p>
            </div>
            <div class="rounded-lg bg-green-50 px-3 py-2">
              <p class="text-xs text-green-700">Paid</p>
              <p class="font-semibold text-green-800">{{ money(inv.paid) }}</p>
            </div>
            <div class="rounded-lg px-3 py-2" :class="inv.days_overdue ? 'bg-red-50' : 'bg-gray-50'">
              <p class="text-xs" :class="inv.days_overdue ? 'text-red-600' : 'text-gray-500'">Remaining</p>
              <p class="font-semibold" :class="inv.days_overdue ? 'text-red-700' : ''">{{ money(inv.outstanding) }}</p>
            </div>
          </div>
          <p class="mt-2 text-right text-xs text-gray-400">{{ inv.currency }}</p>
        </div>

        <section>
          <p class="section-label"><Icon name="cart" :size="14" />Items ({{ inv.items.length }})</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="(i, n) in inv.items" :key="n" class="px-4 py-3">
              <p class="font-medium" dir="auto">{{ i.item_name }}</p>
              <div class="mt-0.5 flex items-center text-xs text-gray-500">
                <span class="flex-1">{{ qty(i.qty) }} {{ i.uom }} × {{ money(i.rate) }}<template v-if="i.discount_percentage"> · −{{ i.discount_percentage }}%</template></span>
                <span class="text-sm font-semibold text-gray-900">{{ money(i.amount) }}</span>
              </div>
            </div>
            <div class="space-y-1 px-4 py-3 text-sm">
              <div v-if="inv.discount_amount" class="flex text-gray-500"><span class="flex-1">Discount</span><span>−{{ money(inv.discount_amount) }}</span></div>
              <div v-for="(t, n) in inv.taxes" :key="'t' + n" class="flex text-gray-500">
                <span class="flex-1">{{ t.description }}<template v-if="t.rate"> {{ t.rate }}%</template><template v-if="t.included"> (included)</template></span>
                <span>{{ money(t.amount) }}</span>
              </div>
              <div class="flex font-semibold"><span class="flex-1">Grand total</span><span>{{ money(inv.grand_total) }}</span></div>
            </div>
          </div>
        </section>

        <section v-if="inv.schedule.length">
          <p class="section-label"><Icon name="calendar" :size="14" />Payment schedule</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="(p, n) in inv.schedule" :key="n" class="flex items-center gap-3 px-4 py-3 text-sm">
              <span class="flex-1">Due {{ day(p.due_date) }}</span>
              <span class="text-gray-500">{{ money(p.amount) }}</span>
              <span class="badge" :class="p.outstanding > 0 ? 'badge-amber' : 'badge-green'">{{ p.outstanding > 0 ? money(p.outstanding) + " left" : "Paid" }}</span>
            </div>
          </div>
        </section>

        <section class="pb-2">
          <p class="section-label"><Icon name="wallet" :size="14" />Paid against this invoice</p>
          <div v-if="!inv.settled_by.length" class="empty"><Icon name="wallet" :size="24" /><p>Nothing paid yet</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <div v-for="p in inv.settled_by" :key="p.kind + p.name" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ p.name }}</p>
                <p class="truncate text-xs text-gray-500">{{ [day(p.posting_date), p.kind, p.mode_of_payment].filter(Boolean).join(" · ") }}</p>
              </div>
              <span class="text-sm font-semibold text-green-700">{{ money(p.amount) }}</span>
            </div>
          </div>
        </section>

        <p v-if="inv.notes" class="card whitespace-pre-line p-4 text-sm text-gray-600" dir="auto">{{ inv.notes }}</p>
      </template>
    </div>
  </div>
</template>
