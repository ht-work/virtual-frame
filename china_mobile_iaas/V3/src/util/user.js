import http from '@/net/http'
import config from '@/util/api_config'
import credential from './credential'

function handlePassword (password) {
  let pwd = window.btoa(password)
  return window.btoa(pwd)
}

function login (name, password, cb) {
  let pwd = handlePassword(password)
  let param = {
    username: name,
    password: pwd
  }
  http.makePost(config.uri.user.login, param, function (err, data) {
    if (!err && data) {
      if (data.code === config.response.code.SUCCESS && data.token) {
        credential.saveCredential(data)
        cb && cb()
      } else {
        // 如果不成功，则返回错误信息
        cb && cb(true, data && data.msg)
      }
    } else {
      cb && cb(err, '网络错误')
    }
  })
}

function changePassword (oldPassword, newPassword, cb) {
  let oldPwd = handlePassword(oldPassword)
  let newPwd = handlePassword(newPassword)
  let param = {
    username: credential.getUserName(),
    password: oldPwd,
    newPassword: newPwd
  }
  http.makePost(config.uri.user.changePassword, param, function (err, data) {
    if (!err && data) {
      if (data.code === config.response.code.SUCCESS) {
        cb && cb()
      } else {
        // 如果不成功，则返回错误信息
        cb && cb(true, data && data.msg)
      }
    } else {
      cb && cb(err, '网络错误')
    }
  })
}

let obj = {
  isAuthed: credential.isAuthed,
  login: login,
  changePassword: changePassword
}
export default obj
