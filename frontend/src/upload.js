const MAX_SIDE = 1600

function shrink(file) {
  if (!file.type.startsWith("image/") || file.type === "image/gif" || file.size < 1.5 * 1024 * 1024) return Promise.resolve(file)
  return new Promise((resolve) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      const k = Math.min(1, MAX_SIDE / Math.max(img.width, img.height))
      const c = document.createElement("canvas")
      c.width = Math.round(img.width * k)
      c.height = Math.round(img.height * k)
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height)
      URL.revokeObjectURL(url)
      c.toBlob((b) => resolve(b ? new File([b], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" }) : file), "image/jpeg", 0.8)
    }
    img.onerror = () => { URL.revokeObjectURL(url); resolve(file) }
    img.src = url
  })
}

export async function uploadFiles(doctype, docname, files) {
  const failed = []
  for (const f of files) {
    try {
      const body = new FormData()
      const file = await shrink(f.file)
      body.append("file", file, file.name)
      body.append("doctype", doctype)
      body.append("docname", docname)
      body.append("is_private", "1")
      const res = await fetch("/api/method/upload_file", {
        method: "POST", body, credentials: "same-origin",
        headers: { Accept: "application/json", "X-Frappe-CSRF-Token": window.csrf_token || "" },
      })
      if (!res.ok) throw new Error(res.status)
    } catch (e) {
      failed.push(f.file.name)
    }
  }
  return failed
}
