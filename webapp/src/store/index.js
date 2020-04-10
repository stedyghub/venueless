import Vue from 'vue'
import Vuex from 'vuex'
import api from 'lib/api'
import chat from './chat'

Vue.use(Vuex)

export default new Vuex.Store({
	state: {
		token: null,
		event: null,
		rooms: null
	},
	actions: {
		login ({state}, token) {
			state.token = token
		},
		connect ({state}) {
			api.connect(state.token)
			api.client.on('joined', (initialState) => {
				state.event = initialState.event
				state.rooms = initialState.rooms
			})
			api.client.on('closed', () => {
				state.event = null
			})
		}
	},
	modules: {
		chat
	}
})
