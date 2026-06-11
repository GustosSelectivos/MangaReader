import api from './api'

export default {
  getCurrent() {
    return api.get('auth/user/')
  }
}
