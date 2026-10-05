// one-off message handed to the next page (e.g. "Password changed" after going back)
let msg = ""
export function setFlash(text) { msg = text }
export function takeFlash() { const m = msg; msg = ""; return m }
