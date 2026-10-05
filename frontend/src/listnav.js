// Remembers the list a detail page was opened from, so the detail page can step to the previous / next record.
import { computed } from "vue"

const lists = {}

export function registerList(kind, paged) {
  lists[kind] = paged
}

export function useListNav(kind, nameFn) {
  const pos = computed(() => {
    const l = lists[kind]
    if (!l) return null
    const names = l.rows.value.map((r) => r.name)
    const i = names.indexOf(nameFn())
    if (i < 0) return null
    return { i, total: names.length, more: !l.done.value, prev: names[i - 1] || null, next: names[i + 1] || null }
  })
  async function nextName() {
    const p = pos.value
    if (!p) return null
    if (p.next) return p.next
    const l = lists[kind]
    if (l.done.value) return null
    await l.more()
    return pos.value && pos.value.next
  }
  return { pos, nextName }
}
