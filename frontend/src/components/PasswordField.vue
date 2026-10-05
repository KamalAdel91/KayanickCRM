<script setup>
import { ref, computed } from "vue"
import Icon from "./Icon.vue"

const model = defineModel({ type: String, default: "" })
const props = defineProps({
  label: String,
  autocomplete: { type: String, default: "new-password" },
  meter: Boolean,
})
const show = ref(false)

// rough client-side hint only; the server enforces the real rules
const strength = computed(() => {
  const v = model.value || ""
  if (!v) return null
  let s = 0
  if (v.length >= 8) s++
  if (v.length >= 12) s++
  if (/[a-z]/.test(v) && /[A-Z]/.test(v)) s++
  if (/\d/.test(v)) s++
  if (/[^A-Za-z0-9]/.test(v)) s++
  if (v.length < 8) return { n: 1, text: "Too short", color: "bg-red-500" }
  if (s <= 2) return { n: 2, text: "Weak", color: "bg-amber-500" }
  if (s <= 3) return { n: 3, text: "Good", color: "bg-brand-600" }
  return { n: 4, text: "Strong", color: "bg-green-600" }
})
</script>

<template>
  <div>
    <label class="label">{{ label }}<span class="text-red-500"> *</span></label>
    <div class="relative">
      <input v-model="model" :type="show ? 'text' : 'password'" :autocomplete="autocomplete"
        class="input pr-10" dir="ltr" autocapitalize="off" spellcheck="false" />
      <button type="button" class="absolute right-1 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center text-gray-400"
        :aria-label="show ? 'Hide password' : 'Show password'" @click="show = !show">
        <Icon :name="show ? 'eye-off' : 'eye'" :size="16" />
      </button>
    </div>
    <div v-if="props.meter && strength" class="mt-2 flex items-center gap-2">
      <div class="flex flex-1 gap-1">
        <span v-for="i in 4" :key="i" class="h-1 flex-1 rounded-full" :class="i <= strength.n ? strength.color : 'bg-gray-200'"></span>
      </div>
      <span class="w-16 text-right text-xs text-gray-500">{{ strength.text }}</span>
    </div>
  </div>
</template>
