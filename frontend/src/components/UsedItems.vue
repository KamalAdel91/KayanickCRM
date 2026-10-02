<script setup>
import { ref } from "vue"
import { call } from "../api"
import Icon from "./Icon.vue"
import PickerSheet from "./PickerSheet.vue"

// used: "" | "Yes" | "No"; items: [{ item_code, item_name, uom, qty }]. Info only, no stock effect.
const used = defineModel("used", { type: String, default: "" })
const items = defineModel("items", { type: Array, default: () => [] })
const picking = ref(false)

async function fetchItems(text) {
  const rows = await call("kayanick_crm.case_api.search_items", { text })
  return rows.map((r) => ({ value: r.name, label: r.item_name || r.name, sub: r.name !== r.item_name ? r.name : r.stock_uom, raw: r }))
}
function pick(r) {
  if (items.value.some((x) => x.item_code === r.value)) return
  items.value.push({ item_code: r.value, item_name: r.raw.item_name || r.value, uom: r.raw.stock_uom, qty: 1 })
}
function unpick(r) { items.value = items.value.filter((x) => x.item_code !== r.value) }
function remove(i) { items.value.splice(i, 1) }
function step(row, d) { row.qty = Math.max(1, (Number(row.qty) || 0) + d) }
</script>

<template>
  <div class="space-y-3">
    <div>
      <p class="label">Did you use products in this case?<span class="text-red-500"> *</span></p>
      <div class="grid grid-cols-2 gap-2">
        <button v-for="o in ['Yes', 'No']" :key="o" type="button" class="btn h-10 border"
          :class="used === o ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white'" @click="used = o">
          <Icon v-if="used === o" name="check" :size="14" />{{ o }}
        </button>
      </div>
    </div>

    <template v-if="used === 'Yes'">
      <div v-for="(row, i) in items" :key="row.item_code" class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2">
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm font-medium" dir="auto">{{ row.item_name }}</span>
          <span class="block truncate text-xs text-gray-500">{{ row.item_code }}<template v-if="row.uom"> · {{ row.uom }}</template></span>
        </span>
        <button type="button" class="btn btn-subtle h-8 w-8 px-0" aria-label="Less" @click="step(row, -1)">−</button>
        <input v-model.number="row.qty" type="number" inputmode="decimal" min="0" step="any" class="input h-8 w-14 px-1 text-center" />
        <button type="button" class="btn btn-subtle h-8 w-8 px-0" aria-label="More" @click="step(row, 1)"><Icon name="plus" :size="14" /></button>
        <button type="button" class="p-1 text-gray-400" aria-label="Remove" @click="remove(i)"><Icon name="x" :size="14" /></button>
      </div>
      <button type="button" class="btn btn-subtle h-10 w-full" @click="picking = true"><Icon name="plus" :size="15" />Add item</button>
      <p class="text-xs text-gray-400">For the record only — stock is not affected.</p>
    </template>

    <PickerSheet v-model:open="picking" title="Used items" placeholder="Search items" multi
      :fetcher="fetchItems" :selected="items.map((x) => x.item_code)" @pick="pick" @unpick="unpick" />
  </div>
</template>
