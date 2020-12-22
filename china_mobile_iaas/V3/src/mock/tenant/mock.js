// import axios from 'axios'
// import MockAdapter from 'axios-mock-adapter'
import apiConfig from '@/util/api_config'
import score_single from './te_score_single.json'
import resourceAssignRatioToNow from './te_resource_assign_ratio_toNow.json'
import busyToNow from './busy__te_busy_toNow.json'
import resourceBusyToNow from './busy__te_resource_busy_toNow.json'
import unbalanceToNow from './unbalance__te_unbalance_toNow.json'
import resourceUnbalanceToNow from './unbalance__te_resource_unbalance_toNow.json'
import scoreToNow from './score__te_score_toNow.json'
import top5AppsJson from './top5_app_ids.json'
import top5AppUnbalance from './top5__te_unbalance.json'
import top5AppCPU from './top5__app_cpu_usage.json'
import top5AppMem from './top5__app_mem_usage.json'
import cmdb_top5Device from '@/mock/app/cmdb_device_ids.json'

let mock

// metric相关

function info_initMetric () {
  let query = 'te_score{tenant="7"}'
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

function usage_metric () {
  let metric = 'te_resource_assign_ratio'
  let buildParam = function (metric) {
    let query = metric + '{tenant="7"}'
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
  let metric1 = 'te_busy'
  let metric2 = 'te_resource_busy'
  let buildParam = function (metric) {
    let query = metric + '{tenant="7"}'
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
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric1)).reply(200, busyToNow)
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric2)).reply(200, resourceBusyToNow)
}

function unbalance_metric () {
  let metric1 = 'te_unbalance'
  let metric2 = 'te_resource_unbalance'
  let buildParam = function (metric) {
    let query = metric + '{tenant="7"}'
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
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric1)).reply(200, unbalanceToNow)
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric2)).reply(200, resourceUnbalanceToNow)
}

function score_metric () {
  let metric = 'te_score'
  let buildParam = function (metric) {
    let query = metric + '{tenant="7"}'
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
  mock.onGet(apiConfig.uri.metric.range, buildParam(metric)).reply(200, scoreToNow)
}

function top5_metric () {
  let metric = 'topk(5,app_unbalance{tenant="7"})'
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
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, top5AppUnbalance)

  let metricForAppCPU = 'app_cpu_usage_avg{tenant="7",app=~"1|2|3|4|5"}'
  mock.onGet(apiConfig.uri.metric.single, buildParam(metricForAppCPU)).reply(200, top5AppCPU)

  let metricForAppMem = 'app_mem_usage_avg{tenant="7",app=~"1|2|3|4|5"}'
  mock.onGet(apiConfig.uri.metric.single, buildParam(metricForAppMem)).reply(200, top5AppMem)
}

function listEntry () {
  let total = 225
  let pageSize = 10
  let totalPage = Math.ceil(total/pageSize)
  let prepareData = function (pageNo) {
    let list = [
      {
        id: '1',
        name: '基础组',
        depart1: '技术部'
      },
      {
        id: '2',
        name: '平台组',
        depart1: '技术部'
      },
      {
        id: '3',
        name: 'IaaS组',
        depart1: '技术部'
      },
      {
        id: '4',
        name: 'PaaS组',
        depart1: '技术部'
      },
      {
        id: '5',
        name: 'SaaS组',
        depart1: '技术部'
      },
      {
        id: '6',
        name: '基础组6',
        depart1: '技术部'
      },
      {
        id: '7',
        name: '平台组7',
        depart1: '技术部'
      },
      {
        id: '8',
        name: 'IaaS组8',
        depart1: '技术部'
      },
      {
        id: '9',
        name: 'PaaS组9',
        depart1: '技术部'
      },
      {
        id: '10',
        name: 'SaaS组10',
        depart1: '技术部'
      }
    ]

    pageNo = pageNo || 1
    let obj = {
      data: list,
      total: total,
      pageNo: pageNo,
      pageSize: pageSize
    }
    if (pageNo !== 1) {
      for (let i in list) {
        let item = list[i]
        item.id = pageNo + item.id
        item.name = item.name + pageNo
        item.depart1 = item.depart1 + pageNo
      }
    }
    return obj
  }
  for (let i = 1; i <= totalPage; i++) {
    mock.onGet(apiConfig.uri.list.tenants, { params: { pageNo: i } }).reply(200, prepareData(i))
  }
}

function top5Apps(){
  let simParam = function (ids) {
    let param = {
      ids: ids
    }
    let obj = {
      params: param
    }
    return obj
  }
  let list = top5AppsJson.data
  let ids = list.map(function (item) {
    return item.id
  })
  ids.sort()
  mock.onGet(apiConfig.uri.list.apps, simParam(ids)).reply(200, top5AppsJson.data)
}

function singleEntry () {
  let id = '7'
  let buildEntry = function (id) {
    let obj = {
      id: id,
      name: '技术平台部',
      department1: 'IT部',
      appCount: 30,
      rp: '哈尔滨资源池',
      cpu: 20 * 512,
      mem: 30 * 2,
      vm: 600,
      bm: 60
    }
    return obj
  }
  mock.onGet(apiConfig.uri.entry.tenant + '/' + id).reply(200, buildEntry(id))
}

function initCMDB () {
  singleEntry()
  listEntry()
  top5Apps()
}

function initMetric () {
  info_initMetric()
  usage_metric()
  busy_metric()
  unbalance_metric()
  score_metric()
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
