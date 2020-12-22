<template>
  <div class="item-info">
    <div class="lc2-header">基本信息</div>
    <div class="item-rows">
      <div class="item-row item-border" v-for="item in items" :key="item.key">
          <span class="item-name">{{item.key}}</span>
          <span class="item-value">{{item.value}}</span>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: 'Info',
  props: ['items'],
  computed: {
    list () {
      return this.items
    }
  }
}
</script>

<style lang="less">
.item-info {
  .item-rows{
    margin-top: 10px;
  }
  .item-row{
    padding: 0 20px;
    min-height: 30px;
    display: flex;
    align-items: center;
    color: #B0B0BF;
    .item-name{
      min-width: 120px;
      max-width: 200px;
      width: 50%;
    }
    .item-value{
      color: #3FFFFE;
      margin-left: 10px;
    }
  }
  .item-row:nth-child(odd) {
    background: rgba(255,255,255,0.05);
  }
}
</style>
