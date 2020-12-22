<template>
  <div class="title-bar">
    <div class="logo" @click="goPage"></div>
    <div class="logo-name" @click="goPage">
      <span>IT云运营综合评估系统</span>
    </div>
    <div v-if="showInfo" class="user-info">
      <UserInfo />
    </div>
  </div>
</template>

<script>
import UserInfo from '../pages/user/User_Info'
import MixinRouter from '@/components/mixin/Mixin_Router'

export default {
  name: 'TitleBar',
  mixins: [MixinRouter],
  components: {
    UserInfo
  },
  props: ['showInfo'],
  methods: {
    goPage () {
      this.golink('main')
    }
  }
}
</script>

<style lang="less">
.title-bar{
  height: 22px;
  position: relative;
  display: flex;
  align-items: center;
  background: #1D1D31;
  color: #FFFFFF;
  width: 100%;
  overflow: hidden;
  .logo{
    cursor: pointer;
    display: inline-block;
    width: 150px;
    height: 22px;
    background-image: url('../../../public/static/img/logo.png');
    background-repeat: no-repeat;
    background-size: auto 100%;
  }
  .logo-name{
    cursor: pointer;
    color: #3DF7F9;
    //font-size: 18px;
    font-weight: bold;
    display: inline-block;
  }
  .user-info{
    position: absolute;
    right: 20px;
    top: 0;
    height: 100%;
  }
}
</style>
