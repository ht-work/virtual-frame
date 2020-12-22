import axios from 'axios'
import credential from '../util/credential'

axios.interceptors.response.use(resp => resp, err => {
  // 统一的错误处理
  let errMsg = err.response && err.response.data && err.response.data.msg
  if (errMsg) {
    console.log(errMsg)
  }
  return Promise.reject(err.response.data)
})

axios.interceptors.request.use(function (config) {
  // 在所有的请求头上加上token
  config.headers.token = credential.getToken()
  return config
}, function (error) {
  // Do something with request error
  return Promise.reject(error)
})

export default axios
