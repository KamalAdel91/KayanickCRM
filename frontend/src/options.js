import { call } from "./api"

// list options + add permissions, fetched once per app session
let pending = null
export function getOptions(refresh = false) {
  if (!pending || refresh) {
    pending = call("kayanick_crm.mobile.get_options").catch((e) => { pending = null; throw e })
  }
  return pending
}
