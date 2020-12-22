<template>
  <div>
    <TitleBar :showInfo='true' />
    <Breadcrumb :breadList="breadList" />
    <Main />
  </div>
</template>

<script>
import Main from '@/components/Page_ResourcePool'
import Breadcrumb from '@/components/common/BreadCrumb'
import TitleBar from '@/components/common/TitleBar'

export default {
  name: 'rpool',
  components: {
    TitleBar,
    Breadcrumb,
    Main
  },
  data () {
    return {
      breadList: [
        { path: '/', name: 'main', value: '首页' },
        { path: '/rpool', name: 'rpool', value: '资源池' }
      ]
    }
  }
}
</script>

<style lang="less">

</style>
