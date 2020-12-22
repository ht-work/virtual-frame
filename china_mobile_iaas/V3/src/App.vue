<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>

export default {
  name: 'app',
  data () {
    return {
    }
  }
}
</script>

<style lang="less">
#app {
  width: 100%;
  height: 100%;
  font-size: 12px;
  background-color: #10103A;
  .lc2-header {
    width: 100%;
    z-index: 10;
    border-radius: 5px;
    height: 23px;
    line-height: 23px;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    background-image: url('../public/static/img/title.svg');
    background-position: center;
    background-repeat: no-repeat;
    >span{
      display: inline-block;
    }
    .text-more{
      cursor: pointer;
      position: absolute;
      right: 0;
    }
  }
  .special-header{
    position: relative;
  }
  .outer-padding{
    padding: 20px;
  }
}
</style>
<style lang="less">
.main-header {
  height: 30px;
  display: flex;
  position: relative;
  margin: 10px 0;
  align-items: center;
  justify-content: center;

  .mh-operation {
    display: inline-block;
    position: absolute;
    right: 10px;
  }

  .mh-middle {
    font-size: 18px;
    line-height: 18px;
    display: inline-block;
  }
}
</style>
<style lang="less">
@color: #f9f9f9;
.info-tooltip{
  display: inline-block;
  height: 20px;
  width: 20px;
  cursor: pointer;
  background-image: url('../public/static/img/info.svg');
  background-size: 100% 100%;
}
.tooltip {
  display: block !important;
  z-index: 10000;

.tooltip-inner {
  background: #2768FF;
  color: white;
  border-radius: 16px;
  padding: 5px 10px 4px;
  width: 600px;
  font-size: 12px;
}

.tooltip-arrow {
  width: 0;
  height: 0;
  border-style: solid;
  position: absolute;
  margin: 5px;
  border-color: black;
  z-index: 1;
}

&[x-placement^="top"] {
   margin-bottom: 5px;

.tooltip-arrow {
  border-width: 5px 5px 0 5px;
  border-left-color: transparent !important;
  border-right-color: transparent !important;
  border-bottom-color: transparent !important;
  bottom: -5px;
  left: calc(50% - 5px);
  margin-top: 0;
  margin-bottom: 0;
}
}

&[x-placement^="bottom"] {
   margin-top: 5px;

.tooltip-arrow {
  border-width: 0 5px 5px 5px;
  border-left-color: transparent !important;
  border-right-color: transparent !important;
  border-top-color: transparent !important;
  top: -5px;
  left: calc(50% - 5px);
  margin-top: 0;
  margin-bottom: 0;
}
}

&[x-placement^="right"] {
   margin-left: 5px;

.tooltip-arrow {
  border-width: 5px 5px 5px 0;
  border-left-color: transparent !important;
  border-top-color: transparent !important;
  border-bottom-color: transparent !important;
  left: -5px;
  top: calc(50% - 5px);
  margin-left: 0;
  margin-right: 0;
}
}

&[x-placement^="left"] {
   margin-right: 5px;

.tooltip-arrow {
  border-width: 5px 0 5px 5px;
  border-top-color: transparent !important;
  border-right-color: transparent !important;
  border-bottom-color: transparent !important;
  right: -5px;
  top: calc(50% - 5px);
  margin-left: 0;
  margin-right: 0;
}
}

&.popover {

.popover-inner {
  background: @color;
  color: black;
  padding: 24px;
  border-radius: 5px;
  box-shadow: 0 5px 30px rgba(black, .1);
}

.popover-arrow {
  border-color: @color;
}
}

&[aria-hidden='true'] {
   visibility: hidden;
   opacity: 0;
   transition: opacity .15s, visibility .15s;
 }

&[aria-hidden='false'] {
   visibility: visible;
   opacity: 1;
   transition: opacity .15s;
 }
}
</style>
