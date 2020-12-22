function getConfig () {
  let prefix = '/api/v1'
  let obj = {
    RefreshInterval: 5 * 60 * 1000, // 5分钟
    SwiperInterval: 5 * 1000, // 轮播间隔：毫秒
    uri: {
      user: {
        login: '/login',
        changePassword: prefix + '/changePassword'
      },
      // 查询单个记录, 格式：/app/id，GET
      entry: {
        device: prefix + '/device',
        app: prefix + '/app',
        tenant: prefix + '/tenant',
        rp: prefix + '/rp'
      },
      list: {
        // 根据id列表查询几个设备数据，格式：/devices，GET，参数：{ids:[id1,id2]}
        devices: prefix + '/devices',
        // 查询全部数据, 格式：/apps，GET
        tenants: prefix + '/tenants',
        apps: prefix + '/apps',
        rps: prefix + '/rps',
        // 查询最新的告警，参数：{ limit: 10}
        latestAlerts: prefix + '/alerts'
      },
      statistics: {
        // 不同级别的告警数量，结果：{urgent: 10, important:20,xx:n}
        alert: prefix + '/stat/alert',
        // 资源池的配额统计信息，可以返回所有资源池的配额列表，前端做累加计算
        rps: prefix + '/stat/rps'
      },
      // 指标查询，提供转发接口即可，转发给Prometheus做处理即可
      metric: {
        single: prefix + '/query',
        range: prefix + '/query_range'
      }
    },
    // 服务器端响应
    response: {
      code: {
        SUCCESS: 0
      }
    }
  }
  return obj
}
let obj = getConfig()
export default obj
