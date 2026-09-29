function errorText(body, status) {
  try {
    if (body._server_messages) {
      const msgs = JSON.parse(body._server_messages).map((m) => JSON.parse(m).message)
      return msgs.join("\n").replace(/<[^>]+>/g, "")
    }
  } catch (e) {}
  if (body.exception) return String(body.exception).split(":").slice(1).join(":").trim() || String(body.exception)
  return "Request failed (" + status + ")"
}

export async function call(method, args = {}, { post = false } = {}) {
  let url = "/api/method/" + method
  const opts = {
    credentials: "same-origin",
    headers: { Accept: "application/json", "X-Frappe-CSRF-Token": window.csrf_token || "" },
  }
  if (post) {
    opts.method = "POST"
    opts.headers["Content-Type"] = "application/json"
    opts.body = JSON.stringify(args)
  } else if (Object.keys(args).length) {
    url += "?" + new URLSearchParams(args).toString()
  }
  let res
  try {
    res = await fetch(url, opts)
  } catch (e) {
    throw new Error("No connection")
  }
  if (res.status === 401) {
    window.location.href = "/login?redirect-to=/kayanick"
    throw new Error("Session expired")
  }
  let body = {}
  try { body = await res.json() } catch (e) {}
  if (!res.ok) throw new Error(errorText(body, res.status))
  return body.message
}
