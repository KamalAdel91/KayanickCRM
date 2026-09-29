export function fmt(d) {
  if (!d) return ""
  return new Date(String(d).slice(0, 10) + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })
}

export function initials(s) {
  return (s || "?").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase()
}

export function localToday() {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

const OUTCOME = { Positive: "badge-green", Negative: "badge-red" }
const LEVEL = { Strong: "badge-green", Medium: "badge-amber", Weak: "badge-red" }
const CHIP = { "badge-green": "border-green-600 bg-green-50 text-green-800", "badge-red": "border-red-500 bg-red-50 text-red-700", "badge-amber": "border-amber-500 bg-amber-50 text-amber-800" }
const DOT = { "badge-green": "bg-green-500", "badge-red": "bg-red-500", "badge-amber": "bg-amber-500" }

export const outcomeBadge = (v) => OUTCOME[v] || "badge-gray"
export const levelBadge = (v) => LEVEL[v] || "badge-gray"
export const chipOn = (badge) => CHIP[badge] || "chip-on"
export const dot = (badge) => DOT[badge] || "bg-gray-400"
