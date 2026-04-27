import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Server, 
  Settings, 
  Activity, 
  AlertTriangle, 
  Zap,
  LogOut,
  Menu,
  X,
  Network,
  Lock
} from 'lucide-react'
import { useState } from 'react'

interface LayoutProps {
  user: any
  onLogout: () => void
  children: React.ReactNode
}

const Layout = ({ user, onLogout, children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: '仪表盘' },
    { path: '/devices', icon: Server, label: '设备管理' },
    { path: '/configs', icon: Settings, label: '配置管理' },
    { path: '/monitoring', icon: Activity, label: '监控' },
    { path: '/alerts', icon: AlertTriangle, label: '告警' },
    { path: '/optimization', icon: Zap, label: '自动优化' },
    { path: '/ztp', icon: Network, label: 'ZTP零接触部署' },
    { path: '/change-password', icon: Lock, label: '修改密码' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 移动端菜单按钮 */}
      <button
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X /> : <Menu />}
      </button>

      {/* 侧边栏 */}
      <aside className={`fixed left-0 top-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 z-40 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold text-gray-800">华为网络运维</h1>
          <p className="text-sm text-gray-500 mt-1">自动化管理系统</p>
        </div>

        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon size={20} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center text-white font-bold">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div>
              <p className="font-medium text-gray-800">{user?.username}</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 w-full px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span>退出登录</span>
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="lg:ml-64 p-6 pt-16 lg:pt-6">
        {children}
      </main>
    </div>
  )
}

export default Layout
