import ax from '@/net/ax'

function makeGet (uri, param, cb) {
  if (param && typeof param === 'function' && !cb) {
    cb = param
    param = null
  }
  ax.get(uri, { params: param })
    .then(function (resp) {
      if (resp && resp.status === 200 && resp.data) {
        cb && cb(resp.data)
      }
    })
}

function makePost (uri, param, cb) {
  if (param && typeof param === 'function' && !cb) {
    cb = param
    param = null
  }
  ax.post(uri, { params: param })
    .then(function (resp) {
      if (resp && resp.status === 200) {
        cb && cb(null, resp.data)
      } else {
        cb && cb(resp)
      }
    })
}

let obj = {
  makeGet: makeGet,
  makePost: makePost
}

export default obj
