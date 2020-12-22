import Vue from 'vue'
import Router from 'vue-router'

import Login from '@/views/0Login'
import Main from '@/views/1Overview'
import ResourcePool from '@/views/2ResourcePool'
import Tenant from '@/views/3Tenant'
import AppSystem from '@/views/4AppSystem'

Vue.use(Router)

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      redirect: '/s'
    },
    {
      path: '/s',
      name: 'main',
      component: Main
    },
    {
      path: '/s/rpool',
      name: 'rpool',
      component: ResourcePool
    },
    {
      path: '/s/tenant',
      name: 'tenant',
      component: Tenant
    },
    {
      path: '/s/app',
      name: 'app',
      component: AppSystem
    },
    {
      path: '/s/login',
      name: 'login',
      component: Login
    }
  ]
})
