import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // On mount, ask the backend "who am I?" using the stored token
    api.get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => {
        // Token expired or invalid — kick them back to login
        localStorage.removeItem('token')
        navigate('/login')
      })
      .finally(() => setLoading(false))
  }, [navigate])

  const handleLogout = async () => {
    // Notify the backend (optional), then destroy the local token
    await api.post('/auth/logout').catch(() => {})
    localStorage.removeItem('token')
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navbar */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-blue-400">3-Tier App</h1>
        <button
          onClick={handleLogout}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm font-semibold transition"
        >
          Logout
        </button>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-8">
        <div className="bg-gray-800 rounded-2xl p-8 shadow-xl">
          <h2 className="text-3xl font-bold mb-2">
            Welcome, <span className="text-blue-400">{user?.username}</span>!
          </h2>
          <p className="text-gray-400 mb-8">You are successfully authenticated.</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 rounded-xl p-5">
              <p className="text-gray-400 text-sm mb-1">Username</p>
              <p className="font-semibold">{user?.username}</p>
            </div>
            <div className="bg-gray-700 rounded-xl p-5">
              <p className="text-gray-400 text-sm mb-1">Email</p>
              <p className="font-semibold">{user?.email}</p>
            </div>
            <div className="bg-gray-700 rounded-xl p-5">
              <p className="text-gray-400 text-sm mb-1">Member since</p>
              <p className="font-semibold">
                {new Date(user?.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Architecture diagram */}
          <div className="mt-8 bg-gray-900 rounded-xl p-6 font-mono text-sm">
            <p className="text-green-400 mb-3">// How your request just traveled:</p>
            <p className="text-blue-300">Browser (React)</p>
            <p className="text-gray-500">   ↓  POST /auth/login</p>
            <p className="text-yellow-300">FastAPI (Python)</p>
            <p className="text-gray-500">   ↓  SELECT * FROM users WHERE username=...</p>
            <p className="text-red-300">PostgreSQL</p>
            <p className="text-gray-500">   ↑  user record</p>
            <p className="text-yellow-300">FastAPI — generates JWT token</p>
            <p className="text-gray-500">   ↑  {"{ access_token: '...' }"}</p>
            <p className="text-blue-300">Browser — stores token, shows dashboard</p>
          </div>
        </div>
      </div>
    </div>
  )
}
