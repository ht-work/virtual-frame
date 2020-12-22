<template>
  <div>
    <div class="alert-rows">
      <div class="alert-row item-border alert-header">
        <span class="item-time">{{headers[0]}}</span>
        <span class="item-deviceIp">{{headers[1]}}</span>
        <span class="item-name">{{headers[2]}}</span>
        <span class="item-level">{{headers[3]}}</span>
        <span class="item-value">{{headers[4]}}</span>
      </div>
      <div class="alert-row item-border" v-for="item in items" :key="item.id">
        <!-- <div class="item-time-icon">
          <span v-bind:class="item.classobj" class="alert-icon"></span>
          <span class="">{{item.time}}</span>
        </div> -->
        <span class="item-time">{{item.time}}</span>
        <span class="item-deviceIp">{{item.device_ip}}</span>
        <span class="item-name">{{item.device_name}}</span>
        <span class="item-level" v-bind:style="{color: item.color}">{{item.level}}</span>
        <span class="item-value">{{item.content}}</span>
      </div>
    </div>
  </div>
</template>

<script>

import MixinTimer from '@/components/mixin/Mixin_Vue_Timer'
import MixinColorCommon from '@/components/mixin/Mixin_Color_Common'
import CMDB from '@/util/cmdb'
import Common from '@/util/common'
import config from '@/util/api_config'

// let timeId

export default {
  name: 'CenterCmp',
  mixins: [MixinTimer, MixinColorCommon],
  data () {
    let obj = {
      headers: ['时间', '设备IP', '设备名称', '级别', '内容'],
      items: []
    }
    return obj
  },
  mounted () {
    this.initTimer(config.RefreshInterval)
    this.loadData && this.loadData()
  },
  methods: {
    getLevelObj () {
      let obj = {
        2: '紧急',
        3: '重要',
        4: '次要',
        5: '一般'
      }
      return obj
    },
    getI18nByKey (key) {
      let levelObj = this.getLevelObj()
      return levelObj[key]
    },
    getColorByLevel (level) {
      let obj = {
        '2': this.getRedColor(),
        '3': this.getYellowColor(),
        '4': this.getGreenColor(),
        '5': this.getLightGreenColor()
      }
      return obj[level]
    },
    getClassByLevel (level) {
      let obj = {
        '2': 'urgent',
        '3': 'important',
        '4': 'lessimportant',
        '5': 'normal'
      }
      return obj[level]
    },
    getSetting (level) {
      let levelObj = this.getLevelObj()
      let setting = {
        color: this.getColorByLevel(level),
        i18n: levelObj[level]
      }
      return setting
    },
    fillColor (list, opt) {
      if (!this.getSetting) {
        throw new Error('need to implement getSetting() method')
      }
      for (let i in list) {
        let item = list[i]
        let level = item.alert_level
        let color = this.getColorByLevel(level)
        let i18n = this.getI18nByKey(level)
        item.classobj = {}
        item.classobj[this.getClassByLevel(level)] = true
        item.level = i18n
        item.color = color
      }
    },
    buildRank (list, opt) {
      for (let i in list) {
        let item = list[i]
        //item.time = new Date(item.alert_start_time).toLocaleString()
        item.time = item.alert_start_time
        item.content = item.moni_index
      }
      if (opt && opt.fillColor) {
        this.fillColor(list)
      }
    },
    // getConfigForRank (data) {
    //   let base = {
    //     header: ['时间', '名称', '级别', '内容'],
    //     // header: ['时间', 'IP', '名称', '级别', '内容'],
    //     data: data,
    //     // index: true,
    //     // rowNum: 5,
    //     columnWidth: [150, 100],
    //     // carousel: 'pages',
    //     align: ['left']
    //   }
    //   return base
    // },
    loadData () {
      let self = this
      CMDB.getLatestAlerts(function (list) {
        if (list) {
          /// ranking data
          self.buildRank(list, { fillColor: true })
          self.items = list
          // self.rankConfig = self.getConfigForRank(rankData)
        }
      })
    }
  }
}
</script>

<style lang="less">
.alert-rows{
  .alert-row{
    display: flex;
    /*justify-content: center;*/
    align-items: center;
    min-height: 30px;
    padding: 0 20px;
    .urgent{
      background-image: url("../../../../../public/static/img/1urgent.svg");
    }
    .important{
      background-image: url("../../../../../public/static/img/2important.svg");
    }
    .lessimportant{
      background-image: url("../../../../../public/static/img/3lessimportant.svg");
    }
    .normal{
      background-image: url("../../../../../public/static/img/4normal.svg");
    }
    .alert-icon{
      width: 16px;
      height: 16px;
      display: inline-block;
    }
    .item-time-icon{
      display: inline-flex;
      align-items: center;
      width: 90px;
      //min-width: 100px;
    }
    .item-time{
      width: 90px;
      margin: 0 5px;
    }
    .item-deviceIp{
      width: 100px;
      margin: 0 5px;
    }
    .item-name{
      width: 100px;
      margin: 0 5px;
    }
    .item-level{
      width: 30px;
      margin: 0 5px;
    }
    .item-value{
      width: 260px;
      margin: 0 5px;
    }
  }
  .alert-row:nth-child(odd) {
    background: rgba(27, 25, 25, 0.05);
  }
}
</style>
