let convertValue = function(v) {
  v = parseFloat(v).toFixed(8)
  v = parseFloat(v).toFixed(2)
  v = parseFloat(v)
  return v
}

function getTime (timeStr) {
  return new Date(timeStr).getTime() / 1000
}

function sortArray (list, fieldName) {
  // use insert sort
  let i, j
  if (list && list.length > 0) {
    for (i = 1; i < list.length; i++) {
      let v = list[i]
      for (j = i - 1; j >= 0; j--) {
        if (fieldName) {
          if (list[j][fieldName] < v[fieldName]) {
            list[j + 1] = list[j]
          } else {
            break
          }
        } else {
          if (list[j] < v) {
            list[j + 1] = list[j]
          } else {
            break
          }
        }
      }
      list[ j + 1 ] = v
    }
  }
  // console.log(list)
  return list
}

var obj = {
  getTime: getTime,
  formatMetricValue: convertValue,
  convertValue: convertValue,
  sortArray: sortArray
}
export default obj
