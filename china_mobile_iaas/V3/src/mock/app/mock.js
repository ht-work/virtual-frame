// import axios from 'axios'
// import MockAdapter from 'axios-mock-adapter'
import apiConfig from '@/util/api_config'

// cmdb
import cmdb_top5Device from './cmdb_device_ids.json'

// metric
import metric_topn_deviceHealth from './metric_topn_device_health.json'
import metric_resource_assign from './metric_app_resource_assign_ratio.json'
import metric_resource_busy from './metric_app_resource_busy.json'
import metric_busy from './metric_app_busy.json'
import metric_health from './metric_app_health.json'
import metric_ha from './metric_app_ha.json'
// 区间查询支持模拟
import range_busy from './time_range_support/range_app_busy.json'
import range_health from './time_range_support/range_app_health.json'
import range_ha from './time_range_support/range_app_ha.json'
import range_resource_assign from './time_range_support/range_app_resource_assign_ratio.json'
import range_resource_busy from './time_range_support/range_app_resource_busy.json'
// metric

let mock

let itemId = 7

// metric相关

//* *******************CMDB********************
function cmdb_single(){
  let buildEntry = function (id) {
    let obj = {
      id: id,
      name: '云平台IaaS',
      tenant: '技术平台部',
      department1: 'IT部',
      rp: '哈尔滨资源池',
      cpu: 20 * 512,
      mem: 30 * 2,
      vm: 600,
      bm: 60
    }
    return obj
  }
  mock.onGet(apiConfig.uri.entry.app + '/' + itemId).reply(200, buildEntry(itemId))
}
function cmdb_list_for_more () {
  let total = 456
  let pageSize = 10
  let totalPage = Math.ceil(total/pageSize)
  let prepareData = function (pageNo) {
    let list = []
    for (let i = 1; i <= 10; i++) {
      list.push({
        id: i + '',
        name: '业务系统' + i,
        department2: '部门' + i,
      })
    }

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
      }
    }
    return obj
  }
  for (let i = 1; i <= totalPage; i++) {
    mock.onGet(apiConfig.uri.list.apps, { params: { pageNo: i } }).reply(200, prepareData(i))
  }
}
function cmdb_top5Devices () {
  let simParam = function (ids) {
    let param = {
      ids: ids
    }
    let obj = {
      params: param
    }
    return obj
  }
  let list = cmdb_top5Device.data
  let ids = list.map(function (item) {
    return item.id
  })
  ids.sort()
  mock.onGet(apiConfig.uri.list.devices, simParam(ids)).reply(200, cmdb_top5Device.data)
}
//* *******************CMDB********************

//* *******************metric********************
function metric_for_line_chart () {
  let assign = 'app_resource_assign_ratio'
  let busy = 'app_busy'
  let resourceBusy = 'app_resource_busy'
  let health = 'app_health'
  let ha = 'app_ha'
  let buildParam = function (metric) {
    let query = metric + '{app="7"}'.replace('7', itemId)
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

  mock.onGet(apiConfig.uri.metric.range, buildParam(assign)).reply(200, metric_resource_assign)
  mock.onGet(apiConfig.uri.metric.range, buildParam(resourceBusy)).reply(200, metric_resource_busy)
  mock.onGet(apiConfig.uri.metric.range, buildParam(busy)).reply(200, metric_busy)
  mock.onGet(apiConfig.uri.metric.range, buildParam(health)).reply(200, metric_health)
  mock.onGet(apiConfig.uri.metric.range, buildParam(ha)).reply(200, metric_ha)
}
function metric_for_time_range_query_support () {
  let assign = 'app_resource_assign_ratio'
  let busy = 'app_busy'
  let resourceBusy = 'app_resource_busy'
  let health = 'app_health'
  let ha = 'app_ha'

  // 当前支持从6月9日到6月10日的查询模拟
  let rangeParam = function (metric) {
    let query = metric + '{app="7"}'.replace('7', itemId)
    let param = {
      query: query,
      start: 1591660800,
      end: 1591747200,
      step: 300
    }
    let obj = {
      params: param
    }
    return obj
  }

  // range query
  mock.onGet(apiConfig.uri.metric.range, rangeParam(assign)).reply(200, range_resource_assign)
  mock.onGet(apiConfig.uri.metric.range, rangeParam(resourceBusy)).reply(200, range_resource_busy)
  mock.onGet(apiConfig.uri.metric.range, rangeParam(busy)).reply(200, range_busy)
  mock.onGet(apiConfig.uri.metric.range, rangeParam(health)).reply(200, range_health)
  mock.onGet(apiConfig.uri.metric.range, rangeParam(ha)).reply(200, range_ha)
}
function metric_topN_health () {
  let deviceHealthBottom = 'bottomk(5,device_health{app="7"})'.replace('7', itemId)
  let buildParam = function (query) {
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.single, buildParam(deviceHealthBottom)).reply(200, metric_topn_deviceHealth)
}
//* *******************metric********************

function initCMDB () {
  cmdb_single()
  cmdb_list_for_more()
  cmdb_top5Devices()
}

function initMetric () {
  metric_topN_health()
  metric_for_line_chart()
  metric_for_time_range_query_support()
}

function init (mockAdapter) {
  mock = mockAdapter
  // CMDB
  initCMDB(mock)
  // metric
  initMetric(mock)
}

export default { init }
