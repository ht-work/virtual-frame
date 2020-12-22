import ttip from '@/util/tooltip'
import router from './Mixin_Router'

var mixin = {
  mixins: [router],
  methods: {
    getTip (key) {
      return ttip.getTip(key)
    },
    getTips (keys) {
      return ttip.getTips(keys)
    }
  }
}

export default mixin
