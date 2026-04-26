import { useState, useEffect } from 'react'
import { configsAPI, devicesAPI } from '../api'
import { Plus, FileText, Play, Trash2 } from 'lucide-react'

const Configs = () => {
  const [devices, setDevices] = useState<any[]>([])
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null)
  const [configs, setConfigs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [newConfig, setNewConfig] = useState({
    device_id: 0,
    config_name: '',
    config_content: '',
    version: '',
  })

  useEffect(() => {
    loadDevices()
  }, [])

  useEffect(() => {
    if (selectedDevice) {
      loadConfigs(selectedDevice)
    }
  }, [selectedDevice])

  const loadDevices = async () => {
    try {
      const response = await devicesAPI.getAll()
      setDevices(response.data)
      if (response.data.length > 0) {
        setSelectedDevice(response.data[0].id)
      }
    } catch (error) {
      console.error('加载设备失败:', error)
    }
  }

  const loadConfigs = async (deviceId: number) => {
    setLoading(true)
    try {
      const response = await configsAPI.getByDevice(deviceId)
      setConfigs(response.data)
    } catch (error) {
      console.error('加载配置失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleActivate = async (configId: number) => {
    try {
      await configsAPI.activate(configId)
      loadConfigs(selectedDevice!)
      alert('配置已激活')
    } catch (error) {
      alert('激活失败')
    }
  }

  const handleDeploy = async (configId: number) => {
    try {
      await configsAPI.deploy(configId)
      alert('配置已部署')
    } catch (error) {
      alert('部署失败')
    }
  }

  const handleDelete = async (configId: number) => {
    if (!confirm('确定要删除此配置吗？')) return
    try {
      await configsAPI.delete(configId)
      loadConfigs(selectedDevice!)
    } catch (error) {
      alert('删除失败')
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await configsAPI.create(newConfig)
      setShowModal(false)
      setNewConfig({
        device_id: 0,
        config_name: '',
        config_content: '',
        version: '',
      })
      loadConfigs(selectedDevice!)
    } catch (error) {
      alert('创建失败')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">配置管理</h1>
          <p className="text-gray-600 mt-1">管理设备配置</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          添加配置
        </button>
      </div>

      {/* 设备选择 */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 mb-2">选择设备</label>
        <select
          value={selectedDevice || ''}
          onChange={(e) => setSelectedDevice(Number(e.target.value))}
          className="input"
        >
          {devices.map((device) => (
            <option key={device.id} value={device.id}>
              {device.name} ({device.ip_address})
            </option>
          ))}
        </select>
      </div>

      {/* 配置列表 */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-800 mb-4">配置列表</h2>
        {loading ? (
          <div className="text-center py-8">加载中...</div>
        ) : configs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无配置</div>
        ) : (
          <div className="space-y-4">
            {configs.map((config) => (
              <div key={config.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <FileText className="text-primary-600" size={20} />
                    <div>
                      <h3 className="font-medium text-gray-800">{config.config_name}</h3>
                      <p className="text-sm text-gray-500">版本: {config.version || '未指定'}</p>
                    </div>
                  </div>
                  {config.is_active && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      当前激活
                    </span>
                  )}
                </div>
                <pre className="bg-gray-50 p-3 rounded text-sm text-gray-700 overflow-x-auto mb-3">
                  {config.config_content.substring(0, 200)}...
                </pre>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleActivate(config.id)}
                    className="btn btn-primary flex items-center gap-2 text-sm"
                  >
                    <Play size={16} />
                    激活
                  </button>
                  <button
                    onClick={() => handleDeploy(config.id)}
                    className="btn btn-secondary flex items-center gap-2 text-sm"
                  >
                    部署
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="btn btn-danger flex items-center gap-2 text-sm"
                  >
                    <Trash2 size={16} />
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 添加配置模态框 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h2 className="text-xl font-bold text-gray-800 mb-4">添加配置</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">设备</label>
                <select
                  value={newConfig.device_id}
                  onChange={(e) => setNewConfig({ ...newConfig, device_id: Number(e.target.value) })}
                  className="input"
                  required
                >
                  <option value="">选择设备</option>
                  {devices.map((device) => (
                    <option key={device.id} value={device.id}>
                      {device.name} ({device.ip_address})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
                <input
                  type="text"
                  value={newConfig.config_name}
                  onChange={(e) => setNewConfig({ ...newConfig, config_name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">版本</label>
                <input
                  type="text"
                  value={newConfig.version}
                  onChange={(e) => setNewConfig({ ...newConfig, version: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">配置内容</label>
                <textarea
                  value={newConfig.config_content}
                  onChange={(e) => setNewConfig({ ...newConfig, config_content: e.target.value })}
                  className="input h-48 font-mono text-sm"
                  placeholder="输入华为设备配置命令..."
                  required
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

export default Configs
