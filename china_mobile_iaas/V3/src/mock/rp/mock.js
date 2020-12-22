import apiConfig from '@/util/api_config'
import score_single from './info__rp_score_single.json'
import resourceAssignRatioToNow from './assign__rp_resource_assign_ratio_toNow.json'
import resourceBusyToNow from './busy__rp_resource_busy_toNow.json'
import cpuUsageToNow from './cpu__rp_cpu_usage_toNow.json'
import memUsageToNow from './mem__rp_cpu_usage_toNow.json'
import cmdb_topNTenantJson from './top5__tenant_ids.json'
import top5TenantQuotaSum from './top5__tenant_quota_sum.json'
import top5TenantResourceQuota from './top5__tenant_resource_quota.json'

let mock

// metric相关

let rpId = '6d40dba3-90a7-11e9-bb30-0242ac110002'
let rpName = '北京池外'

function info_initMetric () {
  let query = 'rp_resource_score{rp="7"}'.replace('7', rpId)
  let buildParam = function (query) {
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.single, buildParam(query)).reply(200, score_single)
}

function assign_metric () {
  let metric = 'rp_resource_assign_ratio'
  let buildParam = function (metric) {
    let query = metric + '{rp="7"}'.replace('7', rpId)
    let now = 1604557325.36
    let defaultStep = 60 * 5
    // 默认查询间隔是1小时
    let defaultQueryRange = 1 * 60 * 60
    let param = {
      query: query,
      start: now - defaultQueryRange,
      end: now,
      step: defaultStep
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric)).reply(200, resourceAssignRatioToNow)
}

function busy_metric () {
  let metric = 'rp_resource_busy'
  let buildParam = function (metric) {
    let query = metric + '{rp="7"}'.replace('7', rpId)
    let now = 1604557325.36
    let defaultStep = 60 * 5
    // 默认查询间隔是1小时
    let defaultQueryRange = 1 * 60 * 60
    let param = {
      query: query,
      start: now - defaultQueryRange,
      end: now,
      step: defaultStep
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric)).reply(200, resourceBusyToNow)
}

function cpu_mem_metric () {
  let metric1 = 'rp_cpu_usage'
  let metric2 = 'rp_mem_usage'
  let buildParam = function (metric) {
    let query = metric + '{rp="7"}'.replace('7', rpId)
    let now = 1604557325.36
    let defaultStep = 60 * 5
    // 默认查询间隔是1小时
    let defaultQueryRange = 1 * 60 * 60
    let param = {
      query: query,
      start: now - defaultQueryRange,
      end: now,
      step: defaultStep
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric1)).reply(200, cpuUsageToNow)
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric2)).reply(200, memUsageToNow)
}

function top5_metric () {
  let metric = 'topk(5,te_quota_sum{rp="7"})'.replace('7', rpId)
  let buildParam = function (metric) {
    let query = metric
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  console.log(JSON.stringify(buildParam(metric)))
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, top5TenantQuotaSum)

  let metricForAppCPUMem = 'te_resource_quota{rp="7",tenant=~"1|2|3|4|5",type=~"VCPU|MEM"}'.replace('7', rpId)
  mock.onGet(apiConfig.uri.metric.single, buildParam(metricForAppCPUMem)).reply(200, top5TenantResourceQuota)
}

function listEntry () {
  // mock.onGet(apiConfig.uri.list.rps).reply(200, rpJson.rows)
}

function cmdb_topNTenant(){
  // CMDB相关
  let simParam = function (ids) {
    let param = {
      ids: ids
    }
    let obj = {
      params: param
    }
    return obj
  }
  let ids = cmdb_topNTenantJson.data.map(function (item) {
    return item.id
  })
  ids.sort()
  mock.onGet(apiConfig.uri.list.tenants, simParam(ids)).reply(200, cmdb_topNTenantJson.data)
}

function singleEntry () {
  let buildEntry = function (id) {
    let obj = {
      id: id,
      name: rpName,
      appCount: 60,
      tenantCount: 40,
      pm: 20000,
      cpu: 20 * 512,
      mem: 30 * 2,
      vm: 600,
      bm: 60
    }
    return obj
  }
  mock.onGet(apiConfig.uri.entry.rp + '/' + rpId).reply(200, buildEntry(rpId))
}

function initCMDB () {
  singleEntry()
  listEntry()
  cmdb_topNTenant()
}

function initMetric () {
  info_initMetric()
  assign_metric()
  busy_metric()
  cpu_mem_metric()
  top5_metric()
}

function init (mockAdapter) {
  mock = mockAdapter
  // CMDB
  initCMDB(mock)
  // metric
  initMetric(mock)
}

export default { init }
