<template>
  <div class="breadcurmb">
    <span class="breadcurmb_item" v-for="(item,index) in breads" :key="index" :style="(index !== breadList.length-1)?'cursor:pointer;':''">
      <span class="breadcurmb_link" @click="goto(index, item)" :style="(index !== 0)?'color:#3EFCFC;':''">{{item.value}}</span>
      <span class="breadcurmb_separator" v-if="index !== breads.length - 1">/</span>
    </span>
  </div>
</template>

<script>
export default {
  name: 'BreadCrumb',
  props: ['breadList'],
  computed: {
    breads () {
      return this.breadList
    }
  },
  methods: {
    goto (index, item) {
      if (index !== this.breads.length - 1) {
        this.$router.push({ path: item.path, name: item.name })
      }
    }
  }
}
</script>

<style lang="less">

.breadcurmb{
  position: absolute;
  left: 0;
  z-index: 1;
  color: white;
  height:36px;
  line-height: 36px;
  padding-left: 16px;
  //width: 100%;
  .breadcurmb_link{
    padding: 0 5px;
  }
}

</style>
