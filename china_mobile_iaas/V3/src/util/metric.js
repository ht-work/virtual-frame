import http from '@/net/http'
import config from '@/util/api_config'
import common from './common'

function buildParam (query, options) {
  options = options || {}
  options.query = query
  return options
}

function doQuery (uri, query, options, cb) {
  if (options && typeof options === 'function' && !cb) {
    cb = options
    options = null
  }
  let param = buildParam(query, options)
  http.makeGet(uri, param, function (data) {
    if (data && data.status === 'success' && data.data.result) {
      cb && cb(data.data.result)
    } else {
      cb && cb()
    }
  })
}

function querySingle (query, options, cb) {
  doQuery(config.uri.metric.single, query, options, cb)
}

function getNow () {
  let now = new Date().getTime() / 1000
  return now
}

function queryRange (query, rangeParam, cb) {
  if (rangeParam && typeof rangeParam === 'function' && !cb) {
    cb = rangeParam
    // 默认点的间隔是5分钟
    let defaultStep = 60 * 5
    // 默认查询间隔是1小时
    let defaultQueryRange = 1 * 60 * 60
    let now = getNow()
    let startTime = now - defaultQueryRange
    rangeParam = {
      start: startTime,
      end: now,
      step: defaultStep
    }
  }
  doQuery(config.uri.metric.range, query, rangeParam, cb)
}

function getDefaultRangeQueryParam () {
  let defaultStep = 60 * 5
  // 默认查询间隔是1小时
  let defaultQueryRange = 1 * 60 * 60
  let now = getNow()
  let startTime = now - defaultQueryRange
  let rangeParam = {
    start: startTime,
    end: now,
    step: defaultStep
  }
  return rangeParam
}

function getSingleMetricValue (query, cb) {
  querySingle(query, function (data) {
    let score = (data && data[0] && data[0].value && data[0].value[1]) || 0
    score = common.formatMetricValue(score)
    cb && cb(score)
  })
}

let obj = {
  getTime: common.getTime,
  querySingle: querySingle,
  queryRange: queryRange,
  getSingleMetricValue: getSingleMetricValue,
  getDefaultRangeQueryParam: getDefaultRangeQueryParam,
  defaultStep: 5 * 60,
  pointerNumber: 12, // 查询多少个点
  name: {
    device: {
      busy: 'device_busy',
      unbalance: 'device_unbalance',
      ha: 'device_ha',
      // bottomN 健康设备（供业务系统页面使用）
      health: 'device_health',
      cpu_usage_avg: 'device_cpu_usage_avg',
      mem_usage_avg: 'device_mem_usage_avg'
    },
    tenant: {
      // 资源使用率
      resource_usage: 'te_resource_assign_ratio',
      //凡是带有avg的，表示是统计租户在各个资源池的平均使用率，凡是带有replace的，表示需要replace掉"{#}"字样
      resource_usage_avg_replace: 'avg(te_resource_assign_ratio{#} <= 99999999) by (tenant, type)',
      // 繁忙度
      busy: 'te_busy', // 总体
      busy_avg_replace: 'avg(te_busy{#} <= 99999999) by (tenant)',
      resource_busy: 'te_resource_busy', // 分类
      // 不平衡度
      unbalance: 'te_unbalance', // 总体
      resource_unbalance: 'te_resource_unbalance', // 分类
      unbalance_avg_replace: 'avg(te_unbalance{#} <= 99999999) by (tenant)',
      // 租户评分
      score: 'te_score',
      score_avg: 'avg(te_score <= 99999999) by (tenant)', // 租户评分（将多个资源池取平均），用于topk计算
      score_avg_replace: "avg(te_score{#} <= 99999999) by (tenant)", //租户评分（将多个资源池取平均）
      usage: 'te_assign_ratio', // 租户使用率，在配额基础上已使用/已分配占比
      usage_avg_replace: 'avg(te_assign_ratio{#}<=100) by (tenant)',
      cpu_score: 'te_cpu', // 租户的CPU评分
      cpu_score_avg_replace: 'avg(te_cpu{#}<=100) by (tenant)',
      mem_score: 'te_mem', // 租户的内存评分
      mem_score_avg_replace: 'avg(te_mem{#}<=100) by (tenant)',
      resource_quota: 'te_resource_quota', // 资源的配额，包含类型参数
      quota_sum: 'te_quota_sum' // 新增指标，用于资源池页面 为VM+BM的配额之和
    },
    app: {
      resource_usage: 'app_resource_assign_ratio',
      busy: 'app_busy',
      resource_busy: 'app_resource_busy',
      health: 'app_health',
      ha: 'app_ha',
      // topN 不平衡业务系统（供租户页面使用）
      unbalance: 'app_unbalance',
      cpu: 'app_cpu_usage_avg',
      mem: 'app_mem_usage_avg'
    },
    rp: {
      resource_assignRatio: 'rp_resource_assign_ratio',
      resource_busy: 'rp_resource_busy',
      cpu: 'rp_cpu_usage',
      mem: 'rp_mem_usage'
    }
  }

}

export default obj
