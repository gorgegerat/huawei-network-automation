import { useState, useEffect } from 'react'
import { 
  Server, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause,
  RefreshCw,
  FileText,
  Network
} from 'lucide-react'

const ZTP = () => {
  const [ztpStatus, setZtpStatus] = useState<any>(null)
  const [templates, setTemplates] = useState<any[]>([])
  const [discoveredDevices, setDiscoveredDevices] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null)

  useEffect(() => {
    loadZTPData()
  }, [])

  const loadZTPData = async () => {
    try {
      const [statusRes, templatesRes, devicesRes] = await Promise.all([
        fetch('/api/ztp/status').then(r => r.json()),
        fetch('/api/ztp/templates').then(r => r.json()),
        fetch('/api/ztp/devices/discovered').then(r => r.json())
      ])
      setZtpStatus(statusRes)
      setTemplates(templatesRes.templates || [])
      setDiscoveredDevices(devicesRes.devices || [])
    } catch (error) {
      console.error('加载ZTP数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartDiscovery = async () => {
    try {
      await fetch('/api/ztp/devices/discovery/start', { method: 'POST' })
      loadZTPData()
    } catch (error) {
      console.error('启动设备发现失败:', error)
    }
  }

  const handleStopDiscovery = async () => {
    try {
      await fetch('/api/ztp/devices/discovery/stop', { method: 'POST' })
      loadZTPData()
    } catch (error) {
      console.error('停止设备发现失败:', error)
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm('确定要删除此模板吗？')) return
    
    try {
      await fetch(`/api/ztp/templates/${templateId}`, { method: 'DELETE' })
      loadZTPData()
    } catch (error) {
      console.error('删除模板失败:', error)
    }
  }

  const handleAssignTemplate = async (macAddress: string, templateId: string) => {
    try {
      await fetch('/api/ztp/devices/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mac_address: macAddress, template_id: templateId })
      })
      loadZTPData()
      setShowAssignModal(false)
    } catch (error) {
      console.error('分配模板失败:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-primary-600" size={32} />
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">ZTP零接触部署</h1>

      {/* ZTP状态 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">ZTP服务</p>
              <p className={`text-lg font-bold ${ztpStatus?.enabled ? 'text-green-600' : 'text-red-600'}`}>
                {ztpStatus?.enabled ? '运行中' : '已停止'}
              </p>
            </div>
            <Server className="text-gray-400" size={24} />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">配置模板</p>
              <p className="text-lg font-bold text-gray-800">{templates.length}</p>
            </div>
            <FileText className="text-gray-400" size={24} />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">发现设备</p>
              <p className="text-lg font-bold text-gray-800">{discoveredDevices.length}</p>
            </div>
            <Network className="text-gray-400" size={24} />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">TFTP服务</p>
              <p className={`text-lg font-bold ${ztpStatus?.tftp_server ? 'text-green-600' : 'text-red-600'}`}>
                {ztpStatus?.tftp_server ? '运行中' : '已停止'}
              </p>
            </div>
            <Server className="text-gray-400" size={24} />
          </div>
        </div>
      </div>

      {/* 设备发现控制 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">设备发现</h2>
          <div className="flex gap-2">
            <button
              onClick={handleStartDiscovery}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Play size={16} />
              启动发现
            </button>
            <button
              onClick={handleStopDiscovery}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              <Pause size={16} />
              停止发现
            </button>
            <button
              onClick={loadZTPData}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              <RefreshCw size={16} />
              刷新
            </button>
          </div>
        </div>

        {discoveredDevices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">MAC地址</th>
                  <th className="text-left py-3 px-4">IP地址</th>
                  <th className="text-left py-3 px-4">厂商</th>
                  <th className="text-left py-3 px-4">首次发现</th>
                  <th className="text-left py-3 px-4">操作</th>
                </tr>
              </thead>
              <tbody>
                {discoveredDevices.map((device) => (
                  <tr key={device.mac_address} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{device.mac_address}</td>
                    <td className="py-3 px-4">{device.ip_address || '-'}</td>
                    <td className="py-3 px-4">{device.vendor}</td>
                    <td className="py-3 px-4">{new Date(device.first_seen).toLocaleString()}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => {
                          setSelectedTemplate(device)
                          setShowAssignModal(true)
                        }}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        分配模板
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">暂无发现的设备</p>
        )}
      </div>

      {/* 配置模板 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">配置模板</h2>
          <button
            onClick={() => setShowTemplateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus size={16} />
            创建模板
          </button>
        </div>

        {templates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div key={template.template_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-gray-800">{template.name}</h3>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {template.device_type}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {template.content.substring(0, 100)}...
                </p>
                <div className="flex gap-2">
                  <button className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                    <Edit size={14} />
                    编辑
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.template_id)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    <Trash2 size={14} />
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">暂无配置模板</p>
        )}
      </div>

      {/* 创建模板模态框 */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-4">创建配置模板</h2>
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">模板ID</label>
                <input
                  type="text"
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="例如: custom_switch"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">模板名称</label>
                <input
                  type="text"
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="例如: 自定义交换机配置"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">设备类型</label>
                <select className="w-full border rounded-lg px-3 py-2">
                  <option value="switch">交换机</option>
                  <option value="router">路由器</option>
                  <option value="firewall">防火墙</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">配置内容</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 h-48 font-mono text-sm"
                  placeholder="输入华为设备配置命令..."
                />
              </div>
            </form>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowTemplateModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                取消
              </button>
              <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 分配模板模态框 */}
      {showAssignModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">分配配置模板</h2>
            <p className="text-gray-600 mb-4">
              为设备 {selectedTemplate.mac_address} 分配配置模板
            </p>
            <div className="space-y-2">
              {templates.map((template) => (
                <button
                  key={template.template_id}
                  onClick={() => handleAssignTemplate(selectedTemplate.mac_address, template.template_id)}
                  className="w-full text-left p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="font-medium">{template.name}</div>
                  <div className="text-sm text-gray-500">{template.device_type}</div>
                </button>
              ))}
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ZTP
