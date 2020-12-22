<template>
  <div class="modal" v-if="showModal">
    <div class="mask"></div>
    <div class="modal-dialog">
      <div class="modal-header">
        <span>修改密码</span>
        <a href="javascript:;" class="icon-close" @click="cancel()"></a>
      </div>
      <div class="modal-body">
        <div>
          <input placeholder="当前密码" type="password" v-model="nowPwd">
        </div>
        <div>
          <input placeholder="新密码" type="password" v-model="newPwd">
        </div>
        <div>
          <input placeholder="确认新密码" type="password" v-model="cfmPwd">
        </div>
      </div>
      <div class="modal-footer">
        <a href="javascript:;" class="btn" @click="ok()">确定</a>
        <a href="javascript:;" class="btn btn-default" @click="cancel()">取消</a>
      </div>
    </div>
  </div>
</template>

<script>
import User from '@/util/user'

export default {
  name: 'LeftChart2',
  props: ['show'],
  computed: {
    showModal () {
      return this.show
    }
  },
  data () {
    let obj = {
      nowPwd: '',
      newPwd: '',
      cfmPwd: ''
    }
    return obj
  },
  methods: {
    cancel () {
      this.$emit('cancel')
    },
    isPasswordOk () {
      return this.nowPwd && this.newPwd && this.newPwd === this.cfmPwd
    },
    success (data) {
      alert('修改密码成功')
    },
    fail (msg) {
      alert(msg)
    },
    ok () {
      // 校验用户密码修改是否成功，不成功的话提示，成功的话也提示
      if (this.isPasswordOk()) {
        let self = this
        User.changePassword(this.nowPwd, this.newPwd, function(err, msg){
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

<style lang="less" scoped>

</style>
