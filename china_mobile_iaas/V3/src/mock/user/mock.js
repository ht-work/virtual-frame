import apiConfig from '@/util/api_config'

let mock

function makePassword (str) {
  return window.btoa(window.btoa(str))
}

function login () {
  let param = {
    params: {
      username: 'admin',
      password: makePassword('admin')
    }
  }
  let response = {
    username: 'admin',
    token: 'abc',
    code: 0
  }
  mock.onPost(apiConfig.uri.user.login, param).reply(200, response)
}

function login_wrong () {
  let param = {
    params: {
      username: 'admin',
      password: makePassword('123')
    }
  }
  let response = {
    username: 'admin',
    code: 0,
    msg: '密码错误：输入的是123，期望的是admin'
  }
  mock.onPost(apiConfig.uri.user.login, param).reply(200, response)
}

// from admin -> admin123
function changepassword () {
  let param = {
    params: {
      username: null,
      password: makePassword('admin'),
      newPassword: makePassword('admin123')
    }
  }
  let response = {
    code: 0,
    msg: 'success'
  }
  mock.onPost(apiConfig.uri.user.changePassword, param).reply(200, response)
}

function changepassword_wrong () {
  let param = {
    params: {
      username: null,
      password: makePassword('admin1'),
      newPassword: makePassword('admin123')
    }
  }
  let response = {
    code: 1,
    msg: '密码错误'
  }
  mock.onPost(apiConfig.uri.user.changePassword, param).reply(200, response)
}

function initCMDB () {
  login()
  login_wrong()
  changepassword()
  changepassword_wrong()
}

function init (mockAdapter) {
  mock = mockAdapter
  // CMDB
  initCMDB(mock)
}

export default { init }
