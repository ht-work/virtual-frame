<template>
<!--  <div>-->
    <div class="operation-container">
      <div class="operation-control" v-show="showControls">
        <span class="operation-time">选择时间</span>
        <date-range-picker
          :dateRange="dateRange"
          @update="onRangeConfirm"
          :locale-data="locale"
          :timePicker="showTimePicker"
          :timePickerIncrement="increment"
          :timePickerSeconds="showTimePicker"
          class="time-picker"
        />
        <span @click="ok" class="time-btn ok-btn">确定</span>
        <span @click="reset" class="time-btn reset-btn">重置</span>
      </div>
      <div class="operation-button" v-on:click="showControls=!showControls"></div>
    </div>
</template>

<script>

import DateRangePicker from 'vue2-daterange-picker'
// you need to import the CSS manually (in case you want to override it)
import 'vue2-daterange-picker/dist/vue2-daterange-picker.css'

export default {
  name: 'Header',
  components: {
    DateRangePicker
  },
  // props: ['title', 'list', 'showList', 'showLink', 'link'],
  data () {
    let obj = {
      showControls: false,
      dateRange: {
        startDate: '2020/11/01',
        endDate: '2020/11/02'
      },
      customMode: false, // customize time range select
      toSubmitDateRange: null,
      showTimePicker: true,
      increment: 1,
      locale: {
        direction: 'ltr', // direction of text
        format: 'yyyy年mm月dd日 HH:MM:ss',
        separator: ' - ', // separator between the two ranges
        applyLabel: '确定',
        cancelLabel: '取消',
        weekLabel: 'W',
        customRangeLabel: 'Custom Range',
        daysOfWeek: '日_一_二_三_四_五_六'.split('_'), // array of days
        monthNames: '1月_2月_3月_4月_5月_6月_7月_8月_9月_10月_11月_12月'.split('_'), // array of month names
        firstDay: 1 // ISO first day of week
      }
    }
    return obj
  },
  methods: {
    onRangeConfirm (value) {
      console.log(value)
      if (value && value.startDate && value.endDate) {
        this.toSubmitDateRange = this.toSubmitDateRange || {}
        this.toSubmitDateRange.startDate = value.startDate
        this.toSubmitDateRange.endDate = value.endDate
      }
    },
    reset () {
      this.customMode = false
      this.submitTimeChange()
    },
    ok () {
      this.customMode = true
      if (!this.toSubmitDateRange) {
        this.toSubmitDateRange = this.toSubmitDateRange || {}
        this.toSubmitDateRange.startDate = this.dateRange.startDate
        this.toSubmitDateRange.endDate = this.dateRange.endDate
      }
      this.submitTimeChange()
    },
    submitTimeChange () {
      let v = {
        customMode: this.customMode,
        dataRange: this.toSubmitDateRange
      }
      this.$emit('rangechange', v)
    }
  }
}
</script>

<style lang="less">
.operation-container {
  text-align: right;
  display: flex;
  align-items: center;
  .operation-control{
    display: inline-block;
    .operation-time{
      color: white;
      margin: 0 10px;
    }
    .border-box-content{
      /*width: 640px;*/
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .reportrange-text{
      padding: 5px 0;
    }
    .time-picker {
      text-align: left;
      color: #0186bb;
    }
    .time-btn{
      background: #298AFF;
      color: #FFFFFF;
      border: 0 solid #9EB7FF;
      cursor: pointer;
      padding: 0 5px;
    }
    .ok-btn{
      margin-left: 10px;
    }
    .reset-btn{
      margin: 0 10px;
    }
  }
  .operation-button {
    display: inline-block;
    text-align: right;
    margin-right: 20px;
    /*margin-bottom: 10px;*/
    height: 20px;
    width: 20px;
    cursor: pointer;
    background-image: url('../../../public/static/img/setting2.png');
    background-size: 100% 100%;
  }
}
</style>

<style lang="less" >
.operation-control{
  .vue-daterange-picker{
    .daterangepicker {
      top: 40px;
      left: 0;
      min-width: 482px;
      .calendars {
        .ranges {
          display: none;
        }
      }
      .drp-buttons{
        .drp-selected{
          //display:none;
        }
      }
    }
  }
}

</style>
