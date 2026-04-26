import { useState, useEffect } from 'react'
import { devicesAPI } from '../api'
import { Plus, Search, RefreshCw, Power, PowerOff } from 'lucide-react'

const Devices = () => {
  const [devices, setDevices] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [newDevice, setNewDevice] = useState({
    name: '',
    ip_address: '',
    device_type: 'switch',
    username: '',
    password: '',
  })

  useEffect(() => {
    loadDevices()
  }, [])

  const loadDevices = async () => {
    try {
      const response = await devicesAPI.getAll()
      setDevices(response.data)
    } catch (error) {
      console.error('加载设备失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (id: number) => {
    try {
      await devicesAPI.connect(id)
      loadDevices()
    } catch (error) {
      alert('连接失败')
    }
  }

  const handleDisconnect = async (id: number) => {
    try {
      await devicesAPI.disconnect(id)
      loadDevices()
    } catch (error) {
      alert('断开连接失败')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此设备吗？')) return
    try {
      await devicesAPI.delete(id)
      loadDevices()
    } catch (error) {
      alert('删除失败')
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await devicesAPI.create(newDevice)
      setShowModal(false)
      setNewDevice({
        name: '',
        ip_address: '',
        device_type: 'switch',
        username: '',
        password: '',
      })
      loadDevices()
    } catch (error) {
      alert('创建失败')
    }
  }

  const filteredDevices = devices.filter(
    (device) =>
      device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.ip_address.includes(searchTerm)
  )

  if (loading) {
    return <div className="text-center py-8">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">设备管理</h1>
          <p className="text-gray-600 mt-1">管理华为网络设备</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          添加设备
        </button>
      </div>

      {/* 搜索栏 */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="搜索设备名称或IP地址..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <button onClick={loadDevices} className="btn btn-secondary flex items-center gap-2">
            <RefreshCw size={20} />
            刷新
          </button>
        </div>
      </div>

      {/* 设备列表 */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 font-medium text-gray-700">设备名称</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">IP地址</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">类型</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">型号</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">状态</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">最后在线</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map((device) => (
                <tr key={device.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4">{device.name}</td>
                  <td className="py-3 px-4 font-mono">{device.ip_address}</td>
                  <td className="py-3 px-4">{device.device_type}</td>
                  <td className="py-3 px-4">{device.model || '-'}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        device.status === 'online'
                          ? 'bg-green-100 text-green-700'
                          : device.status === 'offline'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {device.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {device.last_seen ? new Date(device.last_seen).toLocaleString() : '-'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {device.status === 'online' ? (
                        <button
                          onClick={() => handleDisconnect(device.id)}
                          className="p-2 hover:bg-gray-100 rounded"
                          title="断开连接"
                        >
                          <PowerOff size={18} className="text-red-600" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleConnect(device.id)}
                          className="p-2 hover:bg-gray-100 rounded"
                          title="连接"
                        >
                          <Power size={18} className="text-green-600" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(device.id)}
                        className="p-2 hover:bg-gray-100 rounded"
                        title="删除"
                      >
                        <span className="text-red-600 text-sm">删除</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 添加设备模态框 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-800 mb-4">添加设备</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">设备名称</label>
                <input
                  type="text"
                  value={newDevice.name}
                  onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IP地址</label>
                <input
                  type="text"
                  value={newDevice.ip_address}
                  onChange={(e) => setNewDevice({ ...newDevice, ip_address: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">设备类型</label>
                <select
                  value={newDevice.device_type}
                  onChange={(e) => setNewDevice({ ...newDevice, device_type: e.target.value })}
                  className="input"
                >
                  <option value="switch">交换机</option>
                  <option value="router">路由器</option>
                  <option value="firewall">防火墙</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input
                  type="text"
                  value={newDevice.username}
                  onChange={(e) => setNewDevice({ ...newDevice, username: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                <input
                  type="password"
                  value={newDevice.password}
                  onChange={(e) => setNewDevice({ ...newDevice, password: e.target.value })}
                  className="input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="btn btn-primary flex-1">
                  添加
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn btn-secondary flex-1"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Devices
