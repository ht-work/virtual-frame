// import axios from 'axios'
// import MockAdapter from 'axios-mock-adapter'
import apiConfig from '@/util/api_config'
import rp_busy from './rp/rp__busy.json'
import rp_assign from './rp/rp__assign.json'
import appHealth from './app/app_bottom5_app_health.json'
import appBusy from './app/app__top5__app_busy.json'
import appResourceBusy from './app/app__top5__app_resource_busy.json'
// tenant相关
import te_score from './tenant/ov__tenant_top3_score.json'
import te_usage from './tenant/ov__tenant_usage.json'
import te_cpu from './tenant/ov__tenant_cpu.json'
import te_mem from './tenant/ov__tenant_mem.json'
import te_busy from './tenant/ov__tenant_busy.json'
import te_un from './tenant/ov__tenant_unbalance.json'
//设备指标
// VM
import dev_cpu_vm from './device/vm/device_cpu_avg.json'
import dev_mem_vm from './device/vm/device_mem_avg.json'
import dev_busy_vm from './device/vm/device_top3_busy.json'
import dev_unbalance_vm from './device/vm/device_top3_unbalance.json'
import dev_health_vm from './device/vm/device_bottom3_health.json'
import dev_ha_vm from './device/vm/device_bottom3_ha.json'
// BM
import dev_cpu_bm from './device/bm/device_cpu_avg.json'
import dev_mem_bm from './device/bm/device_mem_avg.json'
import dev_busy_bm from './device/bm/device_top3_busy.json'
import dev_unbalance_bm from './device/bm/device_top3_unbalance.json'
import dev_health_bm from './device/bm/device_bottom3_health.json'
import dev_ha_bm from './device/bm/device_bottom3_ha.json'
// PM
import dev_cpu_pm from './device/pm/device_cpu_avg.json'
import dev_mem_pm from './device/pm/device_mem_avg.json'
import dev_busy_pm from './device/pm/device_top3_busy.json'
import dev_unbalance_pm from './device/pm/device_top3_unbalance.json'
import dev_health_pm from './device/pm/device_bottom3_health.json'
import dev_ha_pm from './device/pm/device_bottom3_ha.json'

// CMDB
import rpJson from '@/data/resourcepool.json'
import latestAlerts from './alert_lastest.json'
import cmdb_top3Tenants from './tenant/ov_CMDB_top3_tenant_ids.json'
import rpStat from './info/rpStat.json'
import deviceVMTop3Json from './device/vm/cmdb_device_top3.json'
import deviceBMTop3Json from './device/bm/cmdb_device_top3.json'
import devicePMTop3Json from './device/pm/cmdb_device_top3.json'
import Metric from '@/util/metric'

let mock

// metric相关

// 资源池繁忙度
function rp_busy_metric () {
  let metric = 'rp_resource_busy'
  let buildParam = function (metric) {
    let query = metric + '{type=~"BM|PM"}'
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, rp_busy)
}
function rp_assign_metric () {
  let metric = 'rp_resource_assign_ratio'
  let buildParam = function (metric) {
    let query = metric + '{type=~"BM|PM"}'
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, rp_assign)
}
// 业务系统相关
function app_metric () {
  let metric = 'bottomk(5,app_health)'
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
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, appHealth)

  let metricBusy = 'topk(5,app_busy)'
  mock.onGet(apiConfig.uri.metric.single, buildParam(metricBusy)).reply(200, appBusy)

  let ids = ['1', '2', '3', '4', '5']
  let types = ['BM', 'VM']
  let metric1 = 'app_resource_busy{app=~"' + ids.join('|') + '",type=~"' + types.join('|') + '"}'
  console.log('mock: ' + metric1)
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric1)).reply(200, appResourceBusy)
}
// 租户相关
function tenant_metric () {
  let metric = 'topk(3,te_score)'
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
  mock.onGet(apiConfig.uri.metric.single, buildParam(metric)).reply(200, te_score)

  let metrics = [Metric.name.tenant.usage, Metric.name.tenant.cpu_score,
    Metric.name.tenant.mem_score, Metric.name.tenant.busy, Metric.name.tenant.unbalance]
  let ids = ['1', '2', '3']
  let jsons = [te_usage, te_cpu, te_mem, te_busy, te_un]
  for (let i = 0; i < metrics.length; i++) {
    let query = metrics[i] + '{tenant=~"' + ids.join('|') + '"}'
    console.log('mock: ' + query)
    mock.onGet(apiConfig.uri.metric.single, buildParam(query)).reply(200, jsons[i])
  }
}

// 设备相关
function device_metric () {
  let ms = ['device_cpu_usage_avg', 'device_mem_usage_avg']
  let types = ['VM', 'BM', 'PM']
  let buildParam = function (metric, type) {
    let query = metric + '{type="' + type + '"}'
    let param = {
      query: query
    }
    let obj = {
      params: param
    }
    return obj
  }
  // vm
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[0], types[0])).reply(200, dev_cpu_vm)
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[1], types[0])).reply(200, dev_mem_vm)
  // bm
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[0], types[1])).reply(200, dev_cpu_bm)
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[1], types[1])).reply(200, dev_mem_bm)
  // pm
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[0], types[2])).reply(200, dev_cpu_pm)
  mock.onGet(apiConfig.uri.metric.single, buildParam(ms[1], types[2])).reply(200, dev_mem_pm)

  // topN指标
  let top3BusyVM = 'topk(3,device_busy{type="VM"})'
  let top3UnVM = 'topk(3,device_unbalance{type="VM"})'
  let bottom3HealthVM = 'bottomk(3,device_health{type="VM"})'
  let bottom3HaVM = 'bottomk(3,device_ha{type="VM"})'
  let simParam = function (metric) {
    let param = {
      query: metric
    }
    let obj = {
      params: param
    }
    return obj
  }
  // VM
  mock.onGet(apiConfig.uri.metric.single, simParam(top3BusyVM)).reply(200, dev_busy_vm)
  mock.onGet(apiConfig.uri.metric.single, simParam(top3UnVM)).reply(200, dev_unbalance_vm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HealthVM)).reply(200, dev_health_vm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HaVM)).reply(200, dev_ha_vm)
  // BM
  mock.onGet(apiConfig.uri.metric.single, simParam(top3BusyVM.replace('VM', 'BM'))).reply(200, dev_busy_bm)
  mock.onGet(apiConfig.uri.metric.single, simParam(top3UnVM.replace('VM', 'BM'))).reply(200, dev_unbalance_bm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HealthVM.replace('VM', 'BM'))).reply(200, dev_health_bm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HaVM.replace('VM', 'BM'))).reply(200, dev_ha_bm)
  // PM
  mock.onGet(apiConfig.uri.metric.single, simParam(top3BusyVM.replace('VM', 'PM'))).reply(200, dev_busy_pm)
  mock.onGet(apiConfig.uri.metric.single, simParam(top3UnVM.replace('VM', 'PM'))).reply(200, dev_unbalance_pm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HealthVM.replace('VM', 'PM'))).reply(200, dev_health_pm)
  mock.onGet(apiConfig.uri.metric.single, simParam(bottom3HaVM.replace('VM', 'PM'))).reply(200, dev_ha_pm)
}

// CMDB相关
// 返回所有资源池
function cmdb_all_rps () {
  mock.onGet(apiConfig.uri.list.rps).reply(200, rpJson.rows)
}

function cmdb_alert () {
  // 告警统计
  let stat_alerts = [
    {
      name: 'urgent',
      value: 5
    },
    {
      name: 'important',
      value: 20
    },
    {
      name: 'lessImportant',
      value: 100
    },
    {
      name: 'normal',
      value: 200
    }
  ]
  mock.onGet(apiConfig.uri.statistics.alert).reply(200, stat_alerts)

  // 最新告警
  let cond = {
    limit: 10
  }
  let param = {
    params: cond
  }
  mock.onGet(apiConfig.uri.list.latestAlerts, param).reply(200, latestAlerts)
}

function cmdb_tenants () {
  let simParam = function (ids) {
    let param = {
      ids: ids
    }
    let obj = {
      params: param
    }
    return obj
  }
  let ids = cmdb_top3Tenants.data.map(function(item){
    return item.id
  }).sort()
  mock.onGet(apiConfig.uri.list.tenants, simParam(ids)).reply(200, cmdb_top3Tenants.data)
}

function cmdb_rpInfo () {
  mock.onGet(apiConfig.uri.statistics.rps).reply(200, rpStat.data)
}

function cmdb_deviceInfo () {
  let simParam = function (ids) {
    let param = {
      ids: ids
    }
    let obj = {
      params: param
    }
    return obj
  }
  let vmIds = ['1', '2', '3']
  let bmIds = ['11', '12', '13']
  let pmIds = ['21', '22', '23']
  mock.onGet(apiConfig.uri.list.devices, simParam(vmIds)).reply(200, deviceVMTop3Json.data)
  mock.onGet(apiConfig.uri.list.devices, simParam(bmIds)).reply(200, deviceBMTop3Json.data)
  mock.onGet(apiConfig.uri.list.devices, simParam(pmIds)).reply(200, devicePMTop3Json.data)
}

function initCMDB () {
  cmdb_all_rps()
  cmdb_alert()
  cmdb_tenants()
  cmdb_rpInfo()
  cmdb_deviceInfo()
}

function initMetric () {
  rp_busy_metric()
  rp_assign_metric()
  app_metric()
  tenant_metric()
  device_metric()
}

function init (mockAdapter) {
  mock = mockAdapter
  // CMDB
  initCMDB(mock)
  // metric
  initMetric(mock)
}

export default { init }
