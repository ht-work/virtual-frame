let mixin = {
  methods: {
    golink (name, option) {
      console.log('name is ' + name)
      if (this.$router && this.$router.push) {
        let obj = option || {}
        obj.name = name
        this.$router.push(obj)
      }
    }
  }
}

export default mixin
