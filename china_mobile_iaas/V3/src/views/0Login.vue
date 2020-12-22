<template>
  <div>
    <TitleBar :showInfo='false' />
    <Main />
  </div>
</template>

<script>
import Main from '@/components/Page_Login'
import TitleBar from '@/components/common/TitleBar'

export default {
  name: 'Login',
  components: {
    TitleBar,
    Main
  }
}
</script>

<style lang="less">
</style>
