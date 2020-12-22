let eventsFuncsMap = {}

function on (eventName, func) {
  let funcs = eventsFuncsMap[eventName]
  if (!funcs) {
    eventsFuncsMap[eventName] = []
  }
  eventsFuncsMap[eventName].push(func)
}

function emit (eventName, param) {
  let funcs = eventsFuncsMap[eventName]
  if (funcs && funcs.length > 0) {
    for (let i = 0; i < funcs.length; i++) {
      funcs[i](param)
    }
  }
}

let obj = {
  EVENTS: {
    APP: 'app_date_range_change',
    TENANT: 'tenant_date_range_change',
    RP: 'rp_date_range_change'
  },
  on: on,
  emit: emit
}
export default obj
