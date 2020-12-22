<template>
  <Overview :items="list" />
</template>

<script>

import Overview from '@/components/common/Overview'
import CMDB from '@/util/cmdb'

export default {
  name: 'Info',
  components: { Overview },
  data () {
    let obj = {
      list: []
    }
    return obj
  },
  mounted () {
    this.loadData()
  },
  methods: {
    buildList (rpStatObj) {
      let list = [
        {
          key: '资源池（个）',
          value: Math.ceil(rpStatObj.rpCount)
        },
        {
          key: '服务租户数（个）',
          value: Math.ceil(rpStatObj.tenantCount)
        },
        {
          key: '承载业务系统数（个）',
          value: Math.ceil(rpStatObj.appCount)
        },
        {
          key: 'KVM宿主机数（台）',
          value: Math.ceil(rpStatObj.PM)
        },
        {
          key: '云主机数量（台）',
          value: Math.ceil(rpStatObj.VM)
        },
        {
          key: '裸金属数量（台）',
          value: Math.ceil(rpStatObj.BM)
        },
        {
          key: 'CPU总数（核）',
          value: Math.ceil(rpStatObj.VCpu)
        },
        {
          key: '内存总数（TB）',
          value: Math.ceil(rpStatObj.MEM)
        }
      ]
      return list
    },
    statRps (rpStatList) {
      let obj = {}
      let fields = ['tenantCount', 'appCount', 'PM', 'VM', 'BM', 'VCpu', 'MEM']
      for (let i = 0; i < rpStatList.length; i++) {
        let item = rpStatList[i]
        for (let j = 0; j < fields.length; j++) {
          let key = fields[j]
          obj[key] = obj[key] || 0
          obj[key] += parseFloat(item[key] || 0)
        }
      }
      obj.rpCount = rpStatList.length
      return obj
    },
    loadData () {
      let self = this
      CMDB.getStatForAllRps(function (data) {
        let obj = self.statRps(data)
        let list = self.buildList(obj)
        self.list = list
      })
    }
  }
}
</script>

<style lang="less">

</style>
