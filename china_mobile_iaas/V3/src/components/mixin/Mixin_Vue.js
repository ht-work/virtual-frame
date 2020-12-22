
var mixin = {
  data () {
    let obj = this.getDataObj()
    return obj
  },
  mounted () {
    this.initTimer(10 * 1000)
  },
  destroyed () {
    this.clearTimer()
  }
}

export default mixin
