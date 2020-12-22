<template>
  <div class="modal" v-if="showModal">
    <div class="mask"></div>
    <div class="modal-dialog">
      <div class="modal-header">
        <span>{{title}}</span>
        <span class="icon-close" @click="cancel()">X</span>
      </div>
      <div class="modal-body">
        <div class="search-area">
          <input :placeholder="searchPlaceHolder" v-model="searchValue"/>
          <a class="btn search-btn" @click="search()">{{searchText}}</a>
        </div>
        <div class="model-item-rows">
          <div class="model-item-row header">
            <span class="model-item-name item-margin">{{dataHeader[0]}}</span>
            <span class="model-item-value item-margin">{{dataHeader[1]}}</span>
          </div>
          <div class="model-item-row" v-for="item in items" :key="item.dataKey"
          @click="select(item.dataKey)" :class="{selected: selectedId === generateKey(item)}">
            <span class="model-item-name item-margin">{{item.department2_orgName_name}}</span>
            <span class="model-item-value item-margin">{{item.department1_orgName_name}}</span>
          </div>
        </div>
        <div class="paging-area">
          <Paging :page-config='pageConfig' @changeCurrentPage="changePage" />
        </div>
      </div>
      <div class="modal-footer">
        <span class="btn btn-default" @click="ok()">{{sureText}}</span>
        <span class="btn" @click="cancel()">{{cancelText}}</span>
      </div>
    </div>
  </div>
</template>

<script>
import MixinMore from '@/components/mixin/Mixin_More'
import Paging from '@/components/common/Paging'
import apiConfig from '@/util/api_config'

export default {
  name: 'LeftChart2',
  mixins: [MixinMore],
  components: {
    Paging
  },
  methods: {
    // 需要单独实现该函数
    goToPage (key) {
      this.golink('tenant', { query: { id: this.parseKey(key)} })
    },
    handleResponseData (data) {
      data.data && (this.items = this.fillKey(data.data))
      let config = {
        total: data.total,
        pageSize: data.pageSize,
        pageNo: data.pageNo
      }
      this.pageConfig = config
    },
    getDataObj () {
      let config = this.getCommonConfig()
      let obj = {
        url: apiConfig.uri.list.tenants,
        title: '请选择租户',
        dataHeader: ['名称', '所属部门']
      }
      for (let key in config) {
        obj[key] = config[key]
      }
      return obj
    },
    generateKey(item){
      return item.department2 + "###" + item.department1_orgName_name;
    },
    parseKey(key){
      return key.substr(0, key.indexOf("###"))
    },
    fillKey(data){
      for (let i in data){
        data[i].dataKey = this.generateKey(data[i]);
      }
      return data;
    }
  }
}
</script>

<style lang="less" scoped>
.model-item-rows{
  .model-item-row{
    .model-item-name{
      width: 40%;
    }
  }
}
</style>
