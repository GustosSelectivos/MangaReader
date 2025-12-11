import api from './api'

export default {
  listProfiles() {
    return api.get('dac/profiles/')
  },
  createProfile(payload) {
    return api.post('dac/profiles/', payload)
  },
  addUserToProfile(profileId, userId) {
    return api.post(`dac/profiles/${profileId}/add-user/`, { user_id: userId })
  },
  removeUserFromProfile(profileId, userId) {
    return api.post(`dac/profiles/${profileId}/remove-user/`, { user_id: userId })
  },
  grantToProfile(profileId, payload) {
    // payload: { codename, model, object_id }
    return api.post(`dac/profiles/${profileId}/grant/`, payload)
  },
  listGrants(profileId) {
    return api.get(`dac/profiles/${profileId}/grants/`)
  }
}
