<template>
  <div>
    <TitleBar :showInfo='true' />
    <Breadcrumb :breadList="breadList" />
    <Main />
  </div>
</template>

<script>
import Breadcrumb from '@/components/common/BreadCrumb'
import Main from '@/components/Page_Tenants'
import TitleBar from '@/components/common/TitleBar'

export default {
  name: 'tenant',
  components: {
    TitleBar,
    Breadcrumb,
    Main
  },
  data () {
    return {
      breadList: [
        { path: '/', name: 'main', value: '首页' },
        { path: '/tenant', name: 'tenant', value: '租户' }
      ]
    }
  }
}
</script>

<style lang="less">
</style>
