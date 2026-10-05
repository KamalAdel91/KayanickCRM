<script setup>
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useListNav } from "../listnav"
import Icon from "./Icon.vue"

// kind: "cases" | "visits"; route: the detail route name
const props = defineProps({ kind: String, route: String })
const r = useRoute()
const router = useRouter()
const { pos, nextName } = useListNav(props.kind, () => r.params.name)
const busy = ref(false)

// replace, so Back still returns to the list instead of stepping through every record
function go(name) {
  if (name) router.replace({ name: props.route, params: { name } })
}
async function next() {
  busy.value = true
  try { go(await nextName()) } finally { busy.value = false }
}
</script>

<template>
  <div v-if="pos && (pos.total > 1 || pos.more)" class="flex items-center gap-2">
    <button type="button" class="btn btn-subtle flex-1" :disabled="!pos.prev" @click="go(pos.prev)">
      <Icon name="chevron-left" :size="16" />Previous
    </button>
    <span class="w-16 text-center text-xs text-gray-500">{{ pos.i + 1 }} / {{ pos.total }}{{ pos.more ? "+" : "" }}</span>
    <button type="button" class="btn btn-subtle flex-1" :disabled="busy || (!pos.next && !pos.more)" @click="next">
      Next<Icon name="chevron-right" :size="16" />
    </button>
  </div>
</template>
