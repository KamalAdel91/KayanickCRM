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
          </div>
          <div class="px-4 py-3">
            <p class="text-xs text-gray-500">Case date</p><p>{{ fmt(c.case_date) }}</p>
          </div>
        </div>

        <section>
          <p class="section-label"><Icon name="clipboard" :size="14" />Items · {{ c.items.length }}</p>
          <div class="card divide-y divide-gray-100">
            <div v-for="i in c.items" :key="i.item_code" class="flex items-center gap-3 px-4 py-2.5">
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium" dir="auto">{{ i.item_name }}</p>
                <p class="truncate text-xs text-gray-400">{{ i.item_code }}</p>
              </div>
              <span class="text-sm font-semibold">{{ i.qty }} <span class="text-xs font-normal text-gray-400">{{ i.uom }}</span></span>
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

      </template>
    </div>
  </div>
</template>
