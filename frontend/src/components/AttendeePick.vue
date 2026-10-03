<script setup>
import { ref } from "vue"
import { call } from "../api"
import PickField from "./PickField.vue"
import PickerSheet from "./PickerSheet.vue"

// null means "me" (the server fills in the logged-in user)
const attendee = defineModel({ type: Object, default: null })
const open = ref(false)

async function fetchUsers(text) {
  const rows = await call("kayanick_crm.case_api.search_attendees", { text })
  return rows.map((u) => ({ value: u.name, label: u.full_name || u.name, sub: u.name, raw: u }))
}
</script>

<template>
  <div>
    <label class="label">Who attended?<span class="text-red-500"> *</span></label>
    <PickField :value="attendee ? attendee.full_name || attendee.name : 'Me'" :sub="attendee ? '' : 'Tap to choose someone else'"
      icon="user" placeholder="Choose who attended" @open="open = true" @clear="attendee = null" />
    <PickerSheet v-model:open="open" title="Who attended?" placeholder="Search reps and managers"
      :fetcher="fetchUsers" @pick="(r) => (attendee = r.raw)" />
  </div>
</template>
