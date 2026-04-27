import { useState, useEffect } from 'react'
import { authAPI } from '../api'
import { useNavigate } from 'react-router-dom'

interface LoginProps {
  onLogin: (user: any) => void
}

const Login = ({ onLogin }: LoginProps) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [captcha, setCaptcha] = useState('')
  const [captchaImage, setCaptchaImage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const navigate = useNavigate()

  // 加载验证码
  const loadCaptcha = async () => {
    try {
      const response = await authAPI.getCaptcha()
      setCaptchaImage(response.data.image)
    } catch (err) {
      console.error('加载验证码失败', err)
    }
  }

  // 组件加载时获取验证码
  useEffect(() => {
    loadCaptcha()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authAPI.login(username, password, captcha)
      const { access_token, user } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      // 检查是否需要强制修改密码
      if (user.must_change_password) {
        setShowChangePassword(true)
        setLoading(false)
        return
      }

      onLogin(user)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败，请检查用户名和密码')
      loadCaptcha() // 刷新验证码
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('未登录')
      }
      await authAPI.changePassword(password, newPassword, token)
      
      // 重新登录
      const response = await authAPI.login(username, newPassword, captcha)
      const { access_token, user } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      onLogin(user)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  if (showChangePassword) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">修改密码</h1>
            <p className="text-yellow-600">首次登录需要修改密码</p>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                新密码
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input"
                placeholder="请输入新密码（至少8位）"
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full py-3 text-lg"
            >
              {loading ? '修改中...' : '修改密码并登录'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">华为网络运维系统</h1>
          <p className="text-gray-600">自动化管理平台</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
              placeholder="请输入用户名"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="请输入密码"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              验证码
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={captcha}
                onChange={(e) => setCaptcha(e.target.value)}
                className="input flex-1"
                placeholder="请输入验证码"
                required
              />
              {captchaImage && (
                <img 
                  src={`data:image/png;base64,${captchaImage}`} 
                  alt="验证码" 
                  className="h-10 cursor-pointer"
                  onClick={loadCaptcha}
                  title="点击刷新验证码"
                />
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full py-3 text-lg"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>默认账号: admin / admin123</p>
          <p className="text-xs mt-2 text-gray-500">连续登录失败5次将锁定账户30分钟</p>
        </div>
      </div>
    </div>
  )
}

export default Login
