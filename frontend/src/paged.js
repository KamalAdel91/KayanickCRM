import { ref } from "vue"
import { call } from "./api"

// Loads a list page by page: reload() starts over, more() appends the next page.
export function usePaged(method, argsFn, size = 50) {
  const rows = ref([])
  const loading = ref(false)
  const done = ref(false)
  const error = ref("")
  let token = 0

  async function load(reset) {
    const t = ++token
    if (reset) { rows.value = []; done.value = false }
    loading.value = true
    error.value = ""
    try {
      const r = await call(method, { args: JSON.stringify({ ...argsFn(), start: rows.value.length, limit: size }) })
      if (t !== token) return
      rows.value = reset ? r : rows.value.concat(r)
      done.value = r.length < size
    } catch (e) {
      if (t === token) error.value = e.message
    } finally {
      if (t === token) loading.value = false
    }
  }
  return { rows, loading, done, error, reload: () => load(true), more: () => load(false) }
}
