var mixin = {
  destroyed () {
    this.clearTimer()
  },
  methods: {
    initTimer (intervalInMs) {
      let that = this
      let newFunc = function () {
        that.refresh && that.refresh()
      }
      this.timerId = setInterval(newFunc, intervalInMs)
    },
    clearTimer () {
      clearInterval(this.timerId)
    },
    refresh () {
      this.loadData && this.loadData()
    }
  }
}

export default mixin
