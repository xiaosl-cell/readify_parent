import { createStore } from 'vuex'

interface State {
  user: {
    token: string | null
    username: string | null
    userId: number | null
  }
}

export default createStore<State>({
  state: {
    user: {
      token: localStorage.getItem('token'),
      username: localStorage.getItem('username'),
      userId: localStorage.getItem('userId') ? Number(localStorage.getItem('userId')) : null
    }
  },
  mutations: {
    SET_USER(state, { token, username, userId }: { token: string; username: string; userId: number }) {
      state.user.token = token
      state.user.username = username
      state.user.userId = userId
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      localStorage.setItem('userId', String(userId))
    },
    CLEAR_USER(state) {
      state.user.token = null
      state.user.username = null
      state.user.userId = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('userId')
    }
  },
  actions: {
    login({ commit }, userData: { token: string; username: string; userId: number }) {
      commit('SET_USER', userData)
    },
    logout({ commit }) {
      commit('CLEAR_USER')
    }
  },
  getters: {
    isLoggedIn: (state) => !!state.user.token,
    username: (state) => state.user.username
  }
})
