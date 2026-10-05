<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { call } from "../api"
import { initials } from "../ui"
import Icon from "../components/Icon.vue"

const route = useRoute()
const router = useRouter()
const me = ref(null)
const error = ref("")
const toast = ref(route.query.done || "")

onMounted(async () => {
  if (toast.value) {
    router.replace({ query: {} })
    setTimeout(() => (toast.value = ""), 3000)
  }
  try { me.value = await call("kayanick_crm.account.get_account") }
  catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <header class="page-head">
      <div class="page-head-inner">
        <h1 class="page-title flex-1">Account</h1>
      </div>
    </header>

    <div class="wrap space-y-4 py-4">
      <div v-if="toast" class="toast"><Icon name="check" :size="16" />{{ toast }}</div>
      <div v-if="error" class="alert"><Icon name="alert" :size="16" /><span>{{ error }}</span></div>
      <div v-if="!me && !error" class="card h-20 animate-pulse"></div>

      <template v-if="me">
        <div class="card flex items-center gap-3 p-4">
          <span class="avatar h-11 w-11 bg-brand-50 text-brand-700">{{ initials(me.full_name) }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold" dir="auto">{{ me.full_name }}</p>
            <p class="truncate text-xs text-gray-500">{{ me.user }}</p>
          </div>
        </div>

        <div class="card divide-y divide-gray-100">
          <router-link to="/change-password" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
            <Icon name="lock" :size="18" class="text-gray-500" />
            <span class="flex-1 font-medium">Change password</span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </router-link>
          <router-link v-if="me.is_admin" to="/admin/reset-password" class="flex items-center gap-3 px-4 py-3 active:bg-gray-50">
            <Icon name="key" :size="18" class="text-gray-500" />
            <span class="min-w-0 flex-1">
              <span class="block font-medium">Reset a user's password</span>
              <span class="block text-xs text-gray-500">Admins only</span>
            </span>
            <Icon name="chevron-right" :size="16" class="text-gray-300" />
          </router-link>
        </div>
      </template>
    </div>
  </div>
</template>
