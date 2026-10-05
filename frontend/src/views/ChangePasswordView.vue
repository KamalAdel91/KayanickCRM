<script setup>
import { ref, computed } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import Icon from "../components/Icon.vue"
import PasswordField from "../components/PasswordField.vue"

const router = useRouter()
const current = ref("")
const next = ref("")
const confirm = ref("")
const logoutOthers = ref(true)
const saving = ref(false)
const error = ref("")

const problem = computed(() => {
  if (!current.value || !next.value || !confirm.value) return "Fill in all three fields"
  if (next.value.length < 8) return "New password must be at least 8 characters"
  if (next.value === current.value) return "New password must be different from the current one"
  if (next.value !== confirm.value) return "New passwords don't match"
  return ""
})

function back() {
  if (window.history.length > 1) router.back()
  else router.push("/account")
}

async function save() {
  error.value = problem.value
  if (error.value) return
  saving.value = true
  try {
    await call("kayanick_crm.account.change_password",
      { old_password: current.value, new_password: next.value, logout_others: logoutOthers.value ? 1 : 0 },
      { post: true })
    router.replace({ name: "account", query: { done: "Password changed" } })
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <button type="button" class="btn btn-subtle w-9 px-0" aria-label="Back" @click="back"><Icon name="chevron-left" :size="18" /></button>
        <h1 class="page-title flex-1">Change password</h1>
      </div>
    </header>

    <form class="wrap space-y-4 py-4" @submit.prevent="save">
      <div class="card space-y-4 p-4">
        <PasswordField v-model="current" label="Current password" autocomplete="current-password" />
        <PasswordField v-model="next" label="New password" meter />
        <PasswordField v-model="confirm" label="Confirm new password" />
        <p v-if="confirm && next !== confirm" class="-mt-2 text-xs text-red-600">Passwords don't match</p>
      </div>

      <label class="card flex items-start gap-3 p-4">
        <input v-model="logoutOthers" type="checkbox" class="mt-0.5 h-4 w-4 accent-gray-900" />
        <span>
          <span class="block text-sm font-medium">Sign out on other devices</span>
          <span class="block text-xs text-gray-500">You'll stay signed in on this phone</span>
        </span>
      </label>

      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <button type="submit" class="btn btn-primary h-11 w-full" :disabled="saving">
        {{ saving ? "Saving…" : "Change password" }}
      </button>
    </form>
  </div>
</template>
