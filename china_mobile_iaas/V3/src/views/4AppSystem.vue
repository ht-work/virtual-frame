<template>
  <div>
    <TitleBar :showInfo='true' />
    <Breadcrumb :breadList="breadList" />
    <Main />
  </div>
</template>

<script>
import Main from '../components/Page_AppSystem.vue'
import Breadcrumb from '@/components/common/BreadCrumb'
import TitleBar from '@/components/common/TitleBar'

export default {
  name: 'app',
  components: {
    TitleBar,
    Breadcrumb,
    Main
  },
  data () {
    return {
      breadList: [
        { path: '/', name: 'main', value: '首页' },
        { path: '/app', name: 'app', value: '业务系统' }
      ]
    }
  }
}
</script>
