<template>
  <div class="profiles-admin">
    <h2>Perfiles (DAC)</h2>

    <div class="create-profile" v-if="isAdmin">
      <input v-model="newProfileName" placeholder="Nombre del perfil" />
      <button @click="createProfile">Crear perfil</button>
    </div>

    <ul>
      <li v-for="p in profiles" :key="p.id">
        <strong>{{ p.name }}</strong>
        <button @click="loadGrants(p.id)">Ver grants</button>
      </li>
    </ul>

    <div v-if="selectedProfile">
      <h3>Grants para: {{ selectedProfile.name }}</h3>
      <ul>
        <li v-for="g in grants" :key="g.id">{{ g.permission.codename }} | {{ g.content_type }} | {{ g.object_id }} | allow: {{ g.allow }}</li>
      </ul>

      <div v-if="isAdmin">
        <h4>Conceder permiso</h4>
        <input v-model="grant.codename" placeholder="codename (p.ej. write)" />
        <input v-model="grant.model" placeholder="model (manga|chapter)" />
        <input v-model="grant.object_id" placeholder="object_id o *" />
        <button @click="grantPermission">Conceder</button>
      </div>
    </div>
  </div>
</template>

<script>
import dacService from '@/services/dacService'
import userService from '@/services/userService'

export default {
  name: 'ProfilesAdminView',
  data() {
    return {
      profiles: [],
      selectedProfile: null,
      grants: [],
      newProfileName: '',
      grant: { codename: '', model: '', object_id: '*' },
      currentUser: null
    }
  },
  computed: {
    isAdmin() {
      // consider site admins (is_staff) as allowed to manage profiles
      return this.currentUser && this.currentUser.is_staff
    }
  },
  async mounted() {
    await this.loadCurrentUser()
    this.loadProfiles()
  },
  methods: {
    async loadCurrentUser() {
      try {
        const res = await userService.getCurrent()
        this.currentUser = res.data.user || (res.data.authenticated ? res.data : null)
      } catch (e) {
        this.currentUser = null
      }
    },
    async loadProfiles() {
      try {
        const res = await dacService.listProfiles()
        this.profiles = res.data
      } catch (e) {
        console.error(e)
      }
    },
    async createProfile() {
      if (!this.newProfileName) return
      try {
        await dacService.createProfile({ name: this.newProfileName })
        this.newProfileName = ''
        await this.loadProfiles()
      } catch (e) {
        alert('Error al crear perfil: ' + (e?.response?.data?.detail || e.message))
      }
    },
    async loadGrants(id) {
      try {
        const res = await dacService.listGrants(id)
        this.grants = res.data
        this.selectedProfile = this.profiles.find(p => p.id === id)
      } catch (e) {
        console.error(e)
      }
    },
    async grantPermission() {
      if (!this.selectedProfile) return
      try {
        await dacService.grantToProfile(this.selectedProfile.id, this.grant)
        await this.loadGrants(this.selectedProfile.id)
      } catch (e) {
        alert('Error al conceder permiso: ' + (e?.response?.data?.detail || e.message))
      }
    }
  }
}
</script>

<style scoped>
.profiles-admin { padding: 1rem }
.create-profile { margin-bottom: 1rem }
button { margin-left: 0.5rem }
</style>
