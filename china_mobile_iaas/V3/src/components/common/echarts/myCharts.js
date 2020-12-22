/**
 * 各种画echarts图表的方法都封装在这里
 * 注意：这里echarts没有采用按需引入的方式，只是为了方便学习
 */

import echarts from 'echarts'
import chinaJson from './china.json'
import rpJson from '@/data/resourcepool.json'
const install = function(Vue) {
  Object.defineProperties(Vue.prototype, {
    $chart: {
      get() {
        return {
          buildMapItem (entry, geoCoord) {
            entry = entry || {}
            entry.value = geoCoord
            return entry
          },
          chinaMap: function (id, options) {
            if (options && options.buildTooltip && options.onItemClick && options.data) {
            } else {
              alert('please provide enough content for the options parameters in chinaMap()')
              return
            }
            if (echarts) {
              echarts.registerMap('china', chinaJson)
            } else {
              alert('echarts is required and should be registered first, but NOT found.')
              return
            }
            let data = options.data
            var geoCoordMap = {
              // 已确认
              '郑州资源池':[113.58, 34.85],  //隶属中原区，id:410102
              '鹿泉资源池':[114.41,38.02], //石家庄鹿泉
              '宁波资源池':[121.08,30.55], /// TODO："id":"3302",需要确定处于哪个区，暂时使用宁波位置
              '石家庄资源池':[114.68,38.23],
              '哈尔滨资源池':[126.63,45.75],
              '呼和浩特资源池':[111.65,40.82],
              '信息港资源池':[116.18, 40.21],  //北京市昌平区，id:110114
              '北京池外': [116.46, 39.92],
              '南基资源池':[113.42, 23.17], //广州天河区，id:440106
              '深圳池外':[114.07,22.62],
              '株洲资源池':[113.53,27.03],
              '杭州湾资源池':[121.08,30.25],  //隶属宁波慈溪，"id": "330282"
              '湘潭资源池':[112.91,27.87],
              '佛山资源池':[113.03,23.10], //广州西南方向
              '汕头资源池':[116.69,23.39],
              '苏州资源池':[120.65,31.40],
              '航空港资源池':[113.57, 34.41]  //隶属新郑市，id:410184
            }
            let self = this
            var convertData = function (data) {
              var res = []
              for (var i = 0; i < data.length; i++) {
                var geoCoord = geoCoordMap[data[i].name]
                if (geoCoord) {
                  let item = self.buildMapItem(data[i], geoCoord)
                  res.push(item)
                }
              }
              return res
            }
            var chart = echarts.init(document.getElementById(id))

            chart.setOption({
              // 此处决定鼠标划过时的内容
              tooltip: {
                formatter: function (param) {
                  return options.buildTooltip(param && param.data)
                }
              },
              cursor: 'pointer',
              // 参考：https://echarts.apache.org/zh/option.html#geo
              geo: {
                map: 'china',
                zoom: 1.2,
                roam: true,
                // 图形上的文本标签，可用于说明图形的一些数据信息，比如值，名称等
                label: {
                  normal: {
                    show: true,
                    // 文字颜色
                    textStyle: {
                      color: 'rgba(0,0,0,0.4)'
                    }
                  }
                },
                // 地图区域的多边形 图形样式。
                itemStyle: {
                  areaColor: 'rgba(4,158,255,0.40)',
                  borderColor: '#049EFF',
                  borderWidth: 1,
                  borderType: 'solid'
                },
                // 地图区域的多边形 图形样式。
                emphasis: {
                  // 高亮状态下的多边形和标签样式。
                  itemStyle: {
                    areaColor: 'rgba(0,252,255,0.80)',
                    borderColor: '#6DFDFF',
                    borderWidth: 1,
                    borderType: 'solid'
                  }
                }
              },
              series: [
                {
                  name: '资源池指标',
                  type: 'scatter',
                  coordinateSystem: 'geo',
                  data: convertData(data),
                  label: {
                    normal: {
                      formatter: '{b}',
                      position: 'right',
                      show: false // 不显示label
                    },
                    emphasis: {
                      show: true
                    }
                  },
                  symbolSize: 10,
                  itemStyle: {
                    shadowColor: 'rgba(0,0,0,0.15)',
                    shadowBlur: 20,
                    shadowOffsetX: 0,
                    shadowOffsetY: 4,
                    color: '#FFBA00'
                    // color: {
                    //   type: 'radial',
                    //   x: 0,
                    //   y: 0,
                    //   r: 3,
                    //   colorStops: [{
                    //     offset: 0, color: '#FFBA00' // 0% 处的颜色
                    //   }, {
                    //     offset: 1, color: 'rgba(255,186,0,0.18)' // 100% 处的颜色
                    //   }],
                    //   global: false // 缺省为 false
                    // }
                    // 使用回调函数，根据分数值来决定颜色
                    // color: function (item) {
                    //   let defaultColor = '#52C41A'
                    //   let col = (options && options.totalColorFunc && options.totalColorFunc(item)) || defaultColor
                    //   return col
                    // }
                    // normal: {
                    //   color: '#FFBA00'
                    // }
                  }
                }
              ]
            })

            chart.on('click', function (param) {
              options.onItemClick(param && param.data)
            })
          }
        }
      }
    }
  })
}

export default {
  install
}
