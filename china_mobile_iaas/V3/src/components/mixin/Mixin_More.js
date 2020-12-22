import http from '@/net/http'

let mixin = {
  props: ['show'],
  computed: {
    showModal () {
      return this.show
    }
  },
  data () {
    return this.getDataObj()
  },
  mounted () {
    this.search()
  },
  methods: {
    golink (name, option) {
      console.log('name is ' + name)
      if (this.$router && this.$router.push) {
        let obj = option || {}
        obj.name = name
        this.$router.push(obj)
      }
    },
    cancel () {
      this.$emit('cancel')
    },
    ok () {
      if (this.selectedId) {
        this.cancel()
        this.goToPage(this.selectedId)
      } else {
        alert('请选择一条记录')
      }
    },
    select (id) {
      this.selectedId = id
    },
    search (pageNo) {
      let param = this.makeQueryParam('name', this.searchValue, pageNo || 1)
      this.doQuery(param)
    },
    makeQueryParam (field, value, pageNumber) {
      let param = {}
      if (field && value) {
        param[field] = value
      }
      param.pageNo = pageNumber || 1
      return param
    },
    doQuery (queryParam) {
      let self = this
      http.makeGet(this.url, queryParam, function(data){
        self.handleResponseData(data)
      })
    },
    changePage (page) {
      this.pageConfig.pageNo = page
      // 重置用户已经选中的记录为空
      this.selectedId = ''
      this.search(page)
    },
    getCommonConfig () {
      let config = {
        sureText: '确定',
        cancelText: '取消',
        searchText: '搜索',
        searchPlaceHolder: '请输入名称',
        pageConfig: {
          total: 0,
          pageSize: 0,
          pageNo: 0
        }
      }
      let obj = {
        searchValue: '',
        selectedId: '',
        items: []
      }
      for (let key in config) {
        obj[key] = config[key]
      }
      return obj
    }
  }
}

export default mixin
