import ttip from '@/util/tooltip'

var mixin = {
  methods: {
    getTip (key) {
      return ttip.getTip(key)
    },
    golink (name, option) {
      console.log('name is ' + name)
      if (this.$router && this.$router.push) {
        let obj = option || {}
        obj.name = name
        this.$router.push(obj)
      }
    },
    getRandom (minV, maxV) {
      let min = minV || 90
      let max = maxV || 100
      let b =Math.floor(Math.random()*(max-min+1)+min)
      return b
    },
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
    sortArray (list, fieldName) {
      // use insert sort
      let i, j
      if (list && list.length > 0) {
        for (i = 1; i < list.length; i++) {
          let v = list[i]
          for (j = i - 1; j >= 0; j--) {
            if (fieldName) {
              if (list[j][fieldName] < v[fieldName]) {
                list[j + 1] = list[j]
              } else {
                break
              }
            } else {
              if (list[j] < v) {
                list[j + 1] = list[j]
              } else {
                break
              }
            }
          }
          list[ j + 1 ] = v
        }
      }
      // console.log(list)
      return list
    },
    refresh () {
      if (!this.getDataObj) {
        throw new Error('please implement getDataObj() method first')
      }
      let obj = this.getDataObj()
      for (let k in obj) {
        this[k] = obj[k]
      }
    }
  }
}

export default mixin
