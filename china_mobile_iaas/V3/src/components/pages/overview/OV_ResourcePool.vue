<template>
  <div class="center-container">
    <div class="map-container">
      <div id="mapChart1"></div>
    </div>
    <div class="busy-container fixed-container">
      <dv-scroll-board :config="rankConfig" class="busy-area"/>
    </div>
  </div>
</template>

<script>

import Mixin from '@/components/mixin/Mixin'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import MixinRouter from '@/components/mixin/Mixin_Router'
import Metric from '@/util/metric'
import CMDB from '@/util/cmdb'
import APIConfig from '@/util/api_config'

export default {
  name: 'CenterCmp',
  mixins: [Mixin, MixinColorCommon, MixinRouter],
  components: {
  },
  data () {
    let obj = {
      timerId: 0,
      rankConfig: null
    }
    return obj
  },
  mounted () {
    this.loadMap()
    this.initTimer(APIConfig.RefreshInterval)
  },
  methods: {
    getRPBusy (cb) {
      let query = Metric.name.rp.resource_busy + '{type=~"BM|PM"}'
      Metric.querySingle(query, function (list) {
        cb && cb('busy', list)
      })
    },
    getRPAssign (cb) {
      let query = Metric.name.rp.resource_assignRatio + '{type=~"BM|PM"}'
      Metric.querySingle(query, function (list) {
        cb && cb('assign', list)
      })
    },
    /*
    list = [
    {
    metric: {__name__: "rp_resource_assign", rp: "huchi1", type: "BM"}
    value: (2) [1604310122.296, "0"]
    }
    ]
    构建以下结构的对象
        resObj =  {
        rpID1:
        {
          metric1:{
            type1:value1,
            type2:value2
          }
          metric2:{
            type:value
          },
          ////以下部分需要等到获取了CMDB中的配置数据后进行补充
          info:{
            app:xx
            tenant:xxx
            rp:xx
          },
          id: xxx,
          name: xx
        }
      }
     */
    formatMetricResponse (list, resObj) {
      resObj = resObj || {}
      for (let i in list) {
        let item = list[i]
        let metric = item.metric
        let values = item.value
        /// TODO: 确保key值一致
        let key = metric.rp
        let rpObj = resObj[key]
        if (!rpObj) {
          rpObj = {}
          resObj[key] = rpObj
        }
        let metricName = metric.__name__
        rpObj[metricName] = rpObj[metricName] || {}
        rpObj[metricName][metric.type] = parseFloat(values[1])
      }
      return resObj
    },
    /// TODO: 此处已经被broken，考虑修复！！！！
    // 查询资源池的繁忙度、分配比数据，返回对象/字典格式数据
    getRPMetricData (cb) {
      let returnObj = {}
      let TASK_COUNT = 2
      let count = 0
      let self = this
      let done = function (metricName, metricList) {
        returnObj[metricName] = metricList
        count++
        if (count >= TASK_COUNT) {
          // 将所有的指标数据拼接成一个数组
          let list = []
          for (let k in returnObj) {
            list = list.concat(returnObj[k])
          }
          let resObj = {}
          // 将指标数组转换成对象形式
          self.formatMetricResponse(list, resObj)
          cb && cb(resObj)
        }
      }
      this.getRPBusy(done)
      this.getRPAssign(done)
    },
    // 准备echarts格式数据
    formatForEcharts (rpList, resObj) {
      for (let i in rpList) {
        let rpInfo = rpList[i]
        /// TODO: 确保key值一致，此处使用id字段
        let key = rpInfo.id
        let obj = resObj[key]
        if (!obj) {
          obj = {}
          resObj[key] = obj
        }
        obj.info = rpInfo
        obj.id = rpInfo.id
        obj.name = rpInfo.name
        obj.type = 'rp'
      }
      // echarts requires array
      let list = []
      for (let key in resObj) {
        list.push(resObj[key])
      }
      return list
    },
    getRPData (cb) {
      let rpList = null
      let resObj = {}
      let TASK_COUNT = 2
      let count = 0
      // 转换成echarts格式数据
      let self = this
      let callback = function () {
        // echarts requires array
        let list = self.formatForEcharts(rpList, resObj)
        cb && cb(list)
      }
      CMDB.getStatForAllRps(function (list) {
        rpList = list
        count++
        if (count === TASK_COUNT) {
          callback && callback()
        }
      })
      this.getRPMetricData(function (metricObj) {
        resObj = metricObj
        count++
        if (count === TASK_COUNT) {
          callback && callback()
        }
      })
    },
    getI18n (key) {
      let obj = {
        VM: '云主机',
        PM: '宿主机',
        BM: '裸金属'
      }
      return obj[key]
    },
    getTooltip (options, item) {
      let html = item.name
      html += '<br />繁忙度：'
      let busy = item.rp_resource_busy
      for (let key in busy) {
        let color = options && options.busyColorFunc(busy[key])
        html += '<br /><span style="margin-left:10px;color:'+color+';">' + this.getI18n(key) + '：' + busy[key].toFixed(2) + '</span>'
      }
      html += '<br />分配率：'
      let assign = item.rp_resource_assign_ratio
      for (let key in assign) {
        let color = options && options.assignColorFunc(assign[key])
        html += '<br /><span style="margin-left:10px;color:'+color+';">' + this.getI18n(key) + '：' + assign[key].toFixed(2) + '</span>'
      }
      return html
    },
    clickItem (item) {
      this.golink('rpool', { query: { id: item.id } })
    },
    loadMap () {
      let self = this
      this.getRPData(function (list) {
        self.loadRanking(list)

        let funcOpts = {
          busyColorFunc: self.getBusyColor,
          assignColorFunc: self.getAssignColor
        }
        let options = {
          buildTooltip: self.getTooltip.bind(null, funcOpts),
          onItemClick: self.clickItem,
          options: {
          },
          data: list
        }
        self.$chart.chinaMap('mapChart1', options)
      })
    },
    // 繁忙度跟颜色的对应关系
    getBusyColor (score) {
      let min_lightgreen = 0; let max_lightgreen = 30
      let min_green = 30; let max_green = 60
      let min_yellow = 60; let max_yellow = 80
      // let min_red = 90, max_red=100;
      let colorStr = ''
      if (min_lightgreen <= score && score < max_lightgreen) {
        colorStr = 'lightgreen'
      } else if (min_green <= score && score < max_green) {
        colorStr = 'green'
      } else if (min_yellow <= score && score < max_yellow) {
        colorStr = 'yellow'
      } else {
        colorStr = 'red'
      }
      return this.getColorByName(colorStr)
    },
    // 分配率跟颜色的对应关系
    getAssignColor (score) {
      let min_lightgreen = 0; let max_lightgreen = 30
      let min_green = 30; let max_green = 80
      let min_yellow = 80; let max_yellow = 90
      // let min_red = 90, max_red=100;
      let colorStr = ''
      if (min_lightgreen <= score && score < max_lightgreen) {
        colorStr = 'lightgreen'
      } else if (min_green <= score && score < max_green) {
        colorStr = 'green'
      } else if (min_yellow <= score && score < max_yellow) {
        colorStr = 'yellow'
      } else {
        colorStr = 'red'
      }
      return this.getColorByName(colorStr)
    },
    // 排名数据展示
    loadRanking (list) {
      /// data#2: ranking data
      let rankData = this.buildRank(list)
      this.rankConfig = this.getConfigForRank(rankData, ['名称', '繁忙度(裸金属)', '繁忙度(KVM宿主机)'])
    },
    buildRank (list) {
      let resList = []
      for (let i in list) {
        /**
         * item = {
         *   id: 20
            info: {name: "北京池外", id: 20}
            name: "北京池外"
            rp_resource_busy: {BM: 15, PM: 16}
            type: "rp"
         * }
         */
        let item = list[i]
        let busyObj = item[Metric.name.rp.resource_busy] && item[Metric.name.rp.resource_busy]
        // let vmBusy = (item[Metric.name.rp.busy] && item[Metric.name.rp.busy].VM) || 0
        let bmBusy = (busyObj && busyObj.BM) || 0
        let pmBusy = (busyObj && busyObj.PM) || 0
        resList.push([ item.name, bmBusy.toFixed(2), pmBusy.toFixed(2) ])
      }
      let newList = this.sortArray(resList, '1')
      return newList
    },
    getConfigForRank (data, headers) {
      let base = {
        header: headers,
        data: data,
        index: false,
        columnWidth: [160, 130, 160],
        align: ['left']
      }
      return base
    },
    refresh () {
      console.log('timer reaches and load data again')
      this.loadMap()
    }
  }
}
</script>

<style lang="less">
.center-container {
  width: 100%;
  height: 100%;
  position: relative;
  .fixed-container {
    position: absolute;
  }
  .busy-container {
    bottom: 0;
    left: 0;
    height: 160px;
    .busy-area{
      height: 100%;
      transform-origin: bottom left;
      transform: scale(0.7, 0.7);
    }
  }
  .usage-container{
    bottom: 0;
    right: 0;
  }
  .map-container {
    width: 100%;
    height: 100%;
    cursor: pointer;
    #mapChart1{
      width:  100%;
      height: 100%;
    }
  }
}
</style>
