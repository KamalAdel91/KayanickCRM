<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { fmt, money } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const d = ref(null)
const error = ref("")
const toast = ref("")

// a payment reminder the rep sends to the customer (WhatsApp or any app), in Arabic, listing the overdue invoices
const reminder = computed(() => {
  if (!d.value) return ""
  const late = d.value.invoices.filter((i) => i.days_overdue)
  if (!late.length) return ""
  const cur = d.value.currency === "EGP" ? "جنيه" : d.value.currency
  const lines = late.map((i) => `• فاتورة ${i.name} بتاريخ ${i.posting_date}: ${money(i.outstanding_amount)} ${cur} (متأخرة ${i.days_overdue} يوم)`)
  return [`السادة ${d.value.customer_name}،`, "تحية طيبة، نود تذكير سيادتكم بالمستحقات المتأخرة:", ...lines,
    `الإجمالي المتأخر: ${money(d.value.overdue)} ${cur}`, "", "شكرًا لتعاونكم",
    [d.value.rep_name, "Kayanick"].filter(Boolean).join(" - ")].join("\n")
})
async function shareReminder() {
  const text = reminder.value
  if (navigator.share) {
    try { await navigator.share({ text }); return } catch (e) { if (e.name === "AbortError") return }
  }
  window.open("https://wa.me/?text=" + encodeURIComponent(text), "_blank")
}
async function copyReminder() {
  try {
    await navigator.clipboard.writeText(reminder.value)
    toast.value = "Reminder copied"
    setTimeout(() => (toast.value = ""), 2500)
  } catch (e) { error.value = "Couldn't copy" }
}

// invoices go back past this year: show the year when it isn't this one
function day(v) {
  if (!v) return ""
  const y = String(v).slice(0, 4)
  return fmt(v) + (y === String(new Date().getFullYear()) ? "" : " " + y)
}

function back() {
  if (window.history.length > 1) router.back()
  else router.push("/debts")
}

onMounted(async () => {
  try { d.value = await call("kayanick_crm.debt_api.get_customer_debt", { customer: route.params.customer }) }
  catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1 truncate" dir="auto">{{ d ? d.customer_name : "Customer" }}</h1>
      </div>
    </header>

    <div class="wrap space-y-4 py-4">
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <template v-if="!d && !error">
        <div v-for="i in 3" :key="i" class="card h-20 animate-pulse"></div>
      </template>

      <template v-if="d">
        <div class="card p-4">
          <p class="text-xs text-gray-500">Owes</p>
          <p class="text-2xl font-semibold" :class="d.balance < 0 ? 'text-green-700' : ''">{{ money(d.balance) }} <span class="text-sm font-medium text-gray-400">{{ d.currency }}</span></p>
          <p v-if="d.rep_name" class="mt-1 flex items-center gap-1 text-xs text-gray-500"><Icon name="user" :size="12" />{{ d.rep_name }}</p>
          <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div class="rounded-lg bg-gray-50 px-3 py-2">
              <p class="text-xs text-gray-500">Open invoices</p>
              <p class="font-semibold">{{ money(d.outstanding) }}</p>
            </div>
            <div class="rounded-lg bg-red-50 px-3 py-2">
              <p class="text-xs text-red-600">Overdue</p>
              <p class="font-semibold text-red-700">{{ money(d.overdue) }}</p>
            </div>
          </div>
          <p v-if="d.unallocated" class="mt-2 text-xs text-gray-500">Less {{ money(d.unallocated) }} paid but not yet matched to an invoice</p>
          <div v-if="reminder" class="mt-3 flex gap-2">
            <button type="button" class="btn btn-primary flex-1" @click="shareReminder"><Icon name="bell" :size="15" />Send payment reminder</button>
            <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Copy reminder" @click="copyReminder"><Icon name="clipboard" :size="16" /></button>
          </div>
        </div>
        <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>

        <section>
          <p class="section-label"><Icon name="file-text" :size="14" />Open invoices</p>
          <div v-if="!d.invoices.length" class="empty"><Icon name="check" :size="24" /><p>No open invoices</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <div v-for="i in d.invoices" :key="i.name" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ i.name }}<span v-if="i.is_return" class="ml-1 text-xs text-gray-400">credit note</span></p>
                <p class="truncate text-xs text-gray-500">{{ day(i.posting_date) }} · due {{ day(i.due_date) }} · of {{ money(i.grand_total) }}</p>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span class="text-sm font-semibold" :class="i.outstanding_amount < 0 ? 'text-green-700' : ''">{{ money(i.outstanding_amount) }}</span>
                <span v-if="i.days_overdue" class="badge" :class="i.days_overdue > 90 ? 'badge-red' : 'badge-amber'">{{ i.days_overdue }}d overdue</span>
                <span v-else-if="i.outstanding_amount > 0" class="badge badge-gray">Not due</span>
              </div>
            </div>
          </div>
        </section>

        <section v-if="d.unallocated_payments.length">
          <p class="section-label"><Icon name="wallet" :size="14" />Paid, not yet matched</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="p in d.unallocated_payments" :key="p.name" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ p.name }}</p>
                <p class="truncate text-xs text-gray-500">{{ [day(p.posting_date), p.mode_of_payment].filter(Boolean).join(" · ") }}</p>
              </div>
              <span class="text-sm font-semibold text-green-700">{{ money(p.unallocated_amount) }}</span>
            </div>
          </div>
        </section>

        <section class="pb-2">
          <p class="section-label"><Icon name="check" :size="14" />Last payments received</p>
          <div v-if="!d.payments.length" class="empty"><Icon name="wallet" :size="24" /><p>No payments yet</p></div>
          <div v-else class="card divide-y divide-gray-100">
            <div v-for="p in d.payments" :key="p.name" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ p.name }}</p>
                <p class="truncate text-xs text-gray-500">{{ [day(p.posting_date), p.mode_of_payment].filter(Boolean).join(" · ") }}</p>
              </div>
              <span class="text-sm font-semibold">{{ money(p.paid_amount) }}</span>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>
