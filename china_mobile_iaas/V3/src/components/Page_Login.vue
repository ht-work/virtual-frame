<template>
  <div id="Login" class="index-container">
    <div class="login-container">
      <div class="login-title">
        <span>账户登录</span>
      </div>
      <div class="login-content">
        <input placeholder="用户名" v-model="name" class="login-name">
        <br />
        <input placeholder="密码" v-model="password" type="password" class="login-pwd">
      </div>
      <div @click="ok" class="login-button">
        <span >登  录</span>
      </div>
    </div>
  </div>
</template>

<script>
import User from '@/util/user'
import MixinRouter from '@/components/mixin/Mixin_Router'
export default {
  name: 'Login',
  mixins: [MixinRouter],
  components: {
  },
  data () {
    return {
      name: '',
      password: ''
    }
  },
  methods: {
    success () {
      this.golink('main')
    },
    fail (msg) {
      alert(msg)
    },
    isNameOk () {
      return this.name !== ''
    },
    isPasswordOk () {
      return this.password !== ''
    },
    ok () {
      if (this.isNameOk() && this.isPasswordOk()) {
        let self = this
        User.login(this.name, this.password, function (err, msg) {
          if (err) {
            self.fail(msg)
          } else {
            self.success()
          }
        })
      }
    }
  }
}
</script>

<style lang="less">
#Login{
  position: absolute;
  width: 100%;
  height: calc(~"100% - 22px");
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('../../public/static/img/bg_login.svg');
  background-repeat: no-repeat;
  .login-container{
    width: 500px;
    height: 330px;
    background-color: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.10);
    .login-title{
      height: 72px;
      display: flex;
      justify-content: center;
      align-items: center;
      border-bottom: 1px solid rgba(0,0,0,0.10);
      color: #00D4D5;
      font-size: 24px;
    }
    .login-content{
      text-align: center;
      font-size: 18px;
      margin: 30px 0;
      >input{
        display: inline-block;
        width: 256px;
        height: 32px;
      }
      >input::placeholder {
        color: rgba(0,0,0,0.25);
      }
      .login-name{
        margin-bottom: 24px;
      }
    }
    .login-button{
      text-align: center;
      cursor: pointer;
      >span{
        display: inline-block;
        background: #00D4D5;
        box-shadow: 0 5px 5px 0 rgba(59,124,255,0.30);
        width: 176px;
        height: 30px;
        font-size: 18px;
        vertical-align: middle;
      }
    }
  }
}
</style>
