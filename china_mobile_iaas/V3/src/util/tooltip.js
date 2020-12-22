import tooltipJson from '@/data/tooltip.json'

function getTip (key) {
  let name = '<b>' + tooltipJson.i18n[key] + '</b>'
  let list = [name, tooltipJson[key]]
  return _arrayToStr(list)
}

function _arrayToStr (list) {
  return list.join('<br />')
}

function getTips (keys) {
  let list = []
  keys.forEach(function (key) {
    list.push(getTip(key))
  })
  return _arrayToStr(list)
}

let obj = {
  getTip: getTip,
  getTips: getTips
}

export default obj
