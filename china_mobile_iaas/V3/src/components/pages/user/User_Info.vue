<template>
  <div style="height: 100%;">
    <div class="user-ops">
      <span @click="showMore" class="user-pwd">修改密码</span>
      <span style="margin-left: 20px;" @click="logout" class="user-exit">退出</span>
    </div>
    <Modal :show="showModal" @cancel="closeMore" />
  </div>
</template>

<script>
import Modal from './User_Change_Password'
import Credential from '@/util/credential'
import MixinRouter from '@/components/mixin/Mixin_Router'

export default {
  name: 'LeftChart2',
  components: {
    Modal
  },
  mixins: [MixinRouter],
  mounted () {
    // 如果未登录，则转到登录页面
    if (!Credential.isAuthed()) {
      this.golink('login')
    }
  },
  data () {
    return {
      showModal: false
    }
  },
  methods: {
    showMore () {
      this.showModal = true
    },
    closeMore () {
      this.showModal = false
    },
    logout () {
      Credential.clearCredential()
      this.golink('login')
    }
  }
}
</script>

<style lang="less">
.user-ops{
  display: flex;
  align-items: center;
  height: 100%;
  >span{
    cursor: pointer;
    text-align: center;
    display: inline-block;
    padding: 0 10px;
  }
  .user-pwd{
    background: #298AFF;
    color: #FFFFFF;
    border: 0 solid #9EB7FF;
  }
  .user-exit{
    background: rgba(255,255,255,0.30);
    border: 0 solid rgba(255,255,255,0.40);
  }
}
</style>
