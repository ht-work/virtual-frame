
var mixin = {
  methods: {
    getRedColor () {
      return '#F86440'
    },
    getGreenColor () {
      return '#298AFF'
    },
    getYellowColor () {
      return '#FFCD2A'
    },
    getLightGreenColor () {
      return '#19D997'
    },
    getColorByName (colorName) {
      let obj = {
        'red': this.getRedColor(),
        'yellow': this.getYellowColor(),
        'green': this.getGreenColor(),
        'lightgreen': this.getLightGreenColor()
      }
      return obj[colorName]
    },
    fillColorString (str, color, fontSizeValue) {
      let stylePrefix = '<span style="color:' + color + ';'
      if (fontSizeValue) {
        stylePrefix += 'font-size:' + fontSizeValue + ';'
      }
      stylePrefix += '">'
      let stylePostfix = '</span>'
      let newStr = stylePrefix + str + stylePostfix
      return newStr
    },
    /***
     *methods need to implement getSetting() method which returns setting obj with given score
     */
    fillColor (list, opt) {
      if (!this.getSetting) {
        throw new Error('need to implement getSetting() method')
      }
      let item
      let i
      let color
      let setting
      //list = [ [name1,score1], [name2,score2], [name3,score3] ]
      for (i in list) {
        // item = [name1, score]
        item = list[i]
        //setting = {score:xxx, color:'red'}
        setting = this.getSetting(item[1])
        color = setting.color
        item[0] = this.fillColorString(item[0], color, opt && opt.fontSize)
        item[1] = this.fillColorString(setting.score, color, opt && opt.fontSize)
      }
      return list
    }
  }
}

export default mixin
