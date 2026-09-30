import { call } from "./api"

// Frappe Cloud push relay (same service Frappe HR uses). "frappe" is a project registered on the relay.
const PROJECT = "frappe"
const TOKEN_KEY = "kc_push_token"

export const pushAvailable = () =>
  !!(window.kc_push_enabled && window.kc_push_relay && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window)

export function pushOn() {
  try { return !!localStorage.getItem(TOKEN_KEY) && Notification.permission === "granted" } catch (e) { return false }
}

async function registration() {
  const reg = await navigator.serviceWorker.register("/kayanick-sw.js", { scope: "/KayanickCRM" })
  if (!reg.active) {
    await new Promise((resolve) => {
      const sw = reg.installing || reg.waiting
      if (!sw) return resolve()
      sw.addEventListener("statechange", () => sw.state === "activated" && resolve())
    })
  }
  return reg
}

async function relayConfig() {
  // fetched through our server: the browser can't always call the relay directly
  return call("kayanick_crm.notify.get_push_config")
}

async function messaging() {
  const [{ initializeApp, getApps }, fm] = await Promise.all([import("firebase/app"), import("firebase/messaging")])
  if (!(await fm.isSupported())) throw new Error("This browser doesn't support push notifications")
  const { config, vapid } = await relayConfig()
  const app = getApps().find((a) => a.name === "kc") || initializeApp(config, "kc")
  return { fm, m: fm.getMessaging(app), vapid }
}

export async function enablePush() {
  const permission = await Notification.requestPermission()
  if (permission !== "granted") throw new Error("Notifications are blocked. Allow them for this site in the browser settings.")
  const reg = await registration()
  const { fm, m, vapid } = await messaging()
  const token = await fm.getToken(m, { vapidKey: vapid, serviceWorkerRegistration: reg })
  const r = await call("frappe.push_notification.subscribe", { fcm_token: token, project_name: PROJECT })
  if (r && r.success === false) throw new Error(r.message || "Could not subscribe")
  try { localStorage.setItem(TOKEN_KEY, token) } catch (e) {}
}

export async function disablePush() {
  let token = null
  try { token = localStorage.getItem(TOKEN_KEY) } catch (e) {}
  if (token) {
    try { await call("frappe.push_notification.unsubscribe", { fcm_token: token, project_name: PROJECT }) } catch (e) {}
    try { const { fm, m } = await messaging(); await fm.deleteToken(m) } catch (e) {}
  }
  try { localStorage.removeItem(TOKEN_KEY) } catch (e) {}
}
