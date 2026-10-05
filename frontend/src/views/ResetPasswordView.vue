<script setup>
import { ref, computed } from "vue"
import { useRouter } from "vue-router"
import { call } from "../api"
import { setFlash } from "../flash"
import Icon from "../components/Icon.vue"
import PickField from "../components/PickField.vue"
import PickerSheet from "../components/PickerSheet.vue"
import PasswordField from "../components/PasswordField.vue"

const router = useRouter()
const user = ref(null)
const pickOpen = ref(false)
const next = ref("")
const confirm = ref("")
const logoutAll = ref(true)
const saving = ref(false)
const error = ref("")

async function fetchUsers(text) {
  const rows = await call("kayanick_crm.account.search_users", { text })
  return rows.map((u) => ({ value: u.name, label: u.full_name || u.name, sub: u.name, raw: u }))
}

const problem = computed(() => {
  if (!user.value) return "Choose a user"
  if (!next.value || !confirm.value) return "Enter the new password twice"
  if (next.value.length < 8) return "Password must be at least 8 characters"
  if (next.value !== confirm.value) return "Passwords don't match"
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
    await call("kayanick_crm.account.admin_reset_password",
      { user: user.value.name, new_password: next.value, logout_all: logoutAll.value ? 1 : 0 },
      { post: true })
    const who = user.value.full_name || user.value.name
    setFlash("Password reset for " + who)
    back()
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
        <h1 class="page-title flex-1">Reset password</h1>
      </div>
    </header>

    <form class="wrap space-y-4 py-4" @submit.prevent="save">
      <div class="card space-y-4 p-4">
        <div>
          <label class="label">User<span class="text-red-500"> *</span></label>
          <PickField :value="user ? user.full_name || user.name : ''" :sub="user ? user.name : ''"
            icon="user" placeholder="Choose a user" @open="pickOpen = true" @clear="user = null" />
        </div>
        <PasswordField v-model="next" label="New password" meter />
        <PasswordField v-model="confirm" label="Confirm new password" />
        <p v-if="confirm && next !== confirm" class="-mt-2 text-xs text-red-600">Passwords don't match</p>
      </div>

      <label class="card flex items-start gap-3 p-4">
        <input v-model="logoutAll" type="checkbox" class="mt-0.5 h-4 w-4 accent-gray-900" />
        <span>
          <span class="block text-sm font-medium">Sign this user out everywhere</span>
          <span class="block text-xs text-gray-500">They'll need the new password on every device</span>
        </span>
      </label>

      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>

      <button type="submit" class="btn btn-primary h-11 w-full" :disabled="saving">
        {{ saving ? "Saving…" : "Reset password" }}
      </button>
    </form>

    <PickerSheet v-model:open="pickOpen" title="Choose a user" placeholder="Search by name or email"
      :fetcher="fetchUsers" @pick="(r) => (user = r.raw)" />
  </div>
</template>
