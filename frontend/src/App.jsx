import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'

// A simple "guard" — if no token, redirect to login.
// Like a bouncer at a VIP section: "Wristband? No? Back to the entrance."
function PrivateRoute({ children }) {
  return localStorage.getItem('token') ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
    </Routes>
  )
}
