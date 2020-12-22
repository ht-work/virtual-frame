import Vue from 'vue'
import App from './App.vue'
import router from './router/index.js'
import './assets/common.less'
import dataV from '@jiaminghi/data-view'
import myCharts from './components/common/echarts/myCharts'
/// import tooltip
import VTooltip from 'v-tooltip'

// import Config from '../config/config.json'
// import mock from './mock/mock'
// if (Config.debugMode) {
//   mock.init()
// }

myCharts.install(Vue)
Vue.use(VTooltip)

Vue.config.productionTip = false

Vue.use(dataV)

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
