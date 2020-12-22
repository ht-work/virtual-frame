var mixin = {
  methods: {
    convertValue (v) {
      v = parseFloat(v).toFixed(8)
      v = parseFloat(v).toFixed(2)
      return v
    },
    getTenantLevel (score) {
      if (0 <= score && score < 60) {
        return 'C'
      } else if (60 <= score && score < 80) {
        return 'B'
      } else if (80 <= score && score <= 100) {
        return 'A'
      } else if (score > 100) {
        return 'A'
      } else {
        return 'INVALID'
      }
    },
    getRpLevel (score) {
      if (0 <= score && score < 60) {
        return 'C'
      } else if (60 <= score && score < 80) {
        return 'B'
      } else if (80 <= score && score <= 100) {
        return 'A'
      } else if (score > 100) {
        return 'A'
      } else {
        return 'INVALID'
      }
    }
  }
}

export default mixin
