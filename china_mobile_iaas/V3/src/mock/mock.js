import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

import AppMock from './app/mock'
import TenantMock from './tenant/mock'
import RpMock from './rp/mock'
import OverviewMock from './ov/mock'
import UserMock from './user/mock'

let mock = new MockAdapter(axios)

function init () {
  TenantMock.init(mock)
  RpMock.init(mock)
  OverviewMock.init(mock)
  AppMock.init(mock)
  UserMock.init(mock)
}

export default { init }
