import http from '@/net/http'
import config from '@/util/api_config'

// *********************列表查询**********************
function getAllRPs (cb) {
  /// TODO: 考虑进行优化，存入sessionStorage，仅查询一次
  http.makeGet(config.uri.list.rps, function (data) {
    cb && cb(data)
  })
}

function getAppsByIds (ids, cb) {
  if (ids instanceof Array) {
    ids = JSON.stringify(ids)
  }
  //console.log("[###]start to get apps by ids.")
  let param = { ids: ids }
  //console.log("[###]param:" + JSON.stringify(param))
  //console.log("[###]url:" + JSON.stringify(config.uri.list.apps))
  http.makeGet(config.uri.list.apps, param, function (data) {
    //console.log("[###]get response:" + JSON.stringify(data))
    cb && cb(data)
    //console.log("[###]get apps by ids done.")
  })
}

function getTenantsByIds (ids, cb) {
  if (ids instanceof Array) {
    ids = JSON.stringify(ids)
  }
  let param = { ids: ids }
  http.makeGet(config.uri.list.tenants, param, function (data) {
    cb && cb(data)
  })
}

function getDeviceByIds (ids, cb) {
  if (ids instanceof Array) {
    ids = JSON.stringify(ids)
  }
  let param = { ids: ids }
  http.makeGet(config.uri.list.devices, param, function (data) {
    if(typeof(data) != 'undefined'){
       for (let i in data){
          data[i].id = data[i].device_id
       }
    }
    cb && cb(data)
  })
}

// 告警查询：最新告警
function getLatestAlerts(cb){
  let defaultCount = 10
  let param = { limit: defaultCount}
  http.makeGet(config.uri.list.latestAlerts, param, function (data) {
    cb && cb(data)
  })
}
// *********************列表查询**********************

// *********************单记录查询**********************
function _getEntryById (uri, id, cb) {
  let url = uri + '/' + id
  http.makeGet(url, function (data) {
    cb && cb(data)
  })
}

function getAppById (id, cb) {
  _getEntryById(config.uri.entry.app, id, cb)
}

function getResourcePoolById (id, cb) {
  _getEntryById(config.uri.entry.rp, id, cb)
}

function getTenantById (id, cb) {
  _getEntryById(config.uri.entry.tenant, id, cb)
}
// *********************单记录查询**********************

// *********************统计查询**********************
function getStatForAlert (cb) {
  http.makeGet(config.uri.statistics.alert, function (data) {
    cb && cb(data)
  })
}
// 获取所有的资源池统计信息
function getStatForAllRps (cb) {
  http.makeGet(config.uri.statistics.rps, function (data) {
    cb && cb(data)
  })
}
// *********************统计查询**********************

let obj = {
  getAllRPs: getAllRPs,
  getDeviceByIds: getDeviceByIds,
  getAppsByIds: getAppsByIds,
  getTenantsByIds: getTenantsByIds,
  getAppById: getAppById,
  getTenantById: getTenantById,
  getResourcePoolById: getResourcePoolById,
  getLatestAlerts: getLatestAlerts,
  getStatForAlert: getStatForAlert,
  getStatForAllRps: getStatForAllRps
}

export default obj
