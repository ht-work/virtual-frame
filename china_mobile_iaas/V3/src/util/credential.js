let creKey = 'credentialKey'

let credentialInfo = null

function saveCredential (credential) {
  if (credential && credential.token) {
    credentialInfo = credential
  } else {
    alert('invalid credential: ' + JSON.stringify(credential))
    return
  }
  if (typeof info !== 'string') {
    credential = JSON.stringify(credential)
  }
  sessionStorage.setItem(creKey, credential)
}

function clearCredential () {
  sessionStorage.removeItem(creKey)
  credentialInfo = null
}

function getCredential () {
  if (!credentialInfo) {
    _loadCredential()
  }
  return credentialInfo
}

function _loadCredential () {
  let str = sessionStorage.getItem(creKey)
  if (str) {
    credentialInfo = JSON.parse(str)
  }
}

function isAuthed () {
  if (!credentialInfo) {
    _loadCredential()
  }
  return credentialInfo
}

function getToken () {
  if (!credentialInfo) {
    _loadCredential()
  }
  return credentialInfo && credentialInfo.token
}

function getUserName () {
  if (!credentialInfo) {
    _loadCredential()
  }
  return credentialInfo && credentialInfo.username
}

var obj = {
  isAuthed: isAuthed,
  getCredential: getCredential,
  saveCredential: saveCredential,
  clearCredential: clearCredential,
  getToken: getToken,
  getUserName: getUserName
}
export default obj
