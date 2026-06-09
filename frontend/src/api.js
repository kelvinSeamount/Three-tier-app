import axios from 'axios'

// Axios is like your waiter — it carries requests to the kitchen (backend)
// and brings back the food (response).
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

// Before every request, attach the JWT token if we have one.
// Like automatically showing your wristband at every bar station.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
