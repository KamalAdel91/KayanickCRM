"""Serves the mobile app's service worker at /kayanick-sw.js.

A service worker only controls pages under its own URL, and files under /assets can't
control /KayanickCRM, so it is served from the site root (registered with scope /KayanickCRM)."""
from werkzeug.wrappers import Response

from frappe.website.page_renderers.base_renderer import BaseRenderer

SW_PATH = "kayanick-sw.js"
ICON = "/kayanick-icon-192.png"
BADGE = "/kayanick-badge.png"

SCRIPT = """
self.addEventListener("install", () => self.skipWaiting())
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()))

self.addEventListener("push", (e) => {
  let p = {}
  try { p = e.data ? e.data.json() : {} } catch (err) { p = { data: { body: e.data && e.data.text() } } }
  const n = p.notification || {}
  const d = p.data || {}
  const title = d.title || n.title || "Kayanick CRM"
  const body = d.body || n.body || ""
  const link = d.click_action || n.click_action || (p.fcmOptions && p.fcmOptions.link) || "/KayanickCRM"
  const tag = d.tag || undefined
  e.waitUntil(self.registration.showNotification(title, {
    body, icon: "%(icon)s", badge: "%(badge)s", tag, renotify: !!tag, timestamp: Date.now(),
    data: { link }, actions: [{ action: "open", title: "Open" }],
  }))
})

self.addEventListener("notificationclick", (e) => {
  e.notification.close()
  const link = (e.notification.data && e.notification.data.link) || "/KayanickCRM"
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
    for (const w of wins) {
      if (w.url.includes("/KayanickCRM") && "focus" in w) { w.navigate(link); return w.focus() }
    }
    return self.clients.openWindow(link)
  }))
})
""" % {"icon": ICON, "badge": BADGE}


class ServiceWorkerRenderer(BaseRenderer):
    def can_render(self):
        return self.path.strip("/") == SW_PATH

    def render(self):
        response = Response(SCRIPT, mimetype="application/javascript")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Service-Worker-Allowed"] = "/KayanickCRM"
        return response
