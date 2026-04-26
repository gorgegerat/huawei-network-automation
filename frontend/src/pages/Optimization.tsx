import { useState, useEffect } from 'react'
import { optimizationAPI, devicesAPI } from '../api'
import { Zap, Play, History, Settings } from 'lucide-react'

const Optimization = () => {
  const [devices, setDevices] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [status, setStatus] = useState<any>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [devicesRes, logsRes, statusRes] = await Promise.all([
        devicesAPI.getAll(),
        optimizationAPI.getLogs({ limit: 20 }),
        optimizationAPI.getStatus(),
      ])
      setDevices(devicesRes.data)
      setLogs(logsRes.data)
      setStatus(statusRes.data)
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }

  const handleTriggerOptimization = async (deviceId: number) => {
    setLoading(true)
    try {
      await optimizationAPI.trigger(deviceId)
      alert('优化已触发')
      loadData()
    } catch (error) {
      alert('触发失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRouteOptimization = async (deviceId: number) => {
    setLoading(true)
    try {
      await optimizationAPI.optimizeRoute(deviceId)
      alert('路由优化已触发')
      loadData()
    } catch (error) {
      alert('路由优化失败')
    } finally {
      setLoading(false)
    }
  }

  const getOptimizationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      route_change: '路由变更',
      bandwidth_adjustment: '带宽调整',
      load_balance: '负载均衡',
    }
    return labels[type] || type
  }

  const getResultColor = (result: string) => {
    switch (result) {
      case 'success':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">自动优化</h1>
        <p className="text-gray-600 mt-1">网络自动优化管理</p>
      </div>

      {/* 优化状态 */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Settings className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold text-gray-800">优化状态</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-700">自动优化</span>
            <span className={`font-medium ${status.enabled ? 'text-green-600' : 'text-gray-500'}`}>
              {status.enabled ? '已启用' : '已禁用'}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-700">检查间隔</span>
            <span className="font-medium text-gray-800">{status.check_interval}秒</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-700">路由优化</span>
            <span className={`font-medium ${status.route_optimization ? 'text-green-600' : 'text-gray-500'}`}>
              {status.route_optimization ? '已启用' : '已禁用'}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-700">带宽管理</span>
            <span className={`font-medium ${status.bandwidth_management ? 'text-green-600' : 'text-gray-500'}`}>
              {status.bandwidth_management ? '已启用' : '已禁用'}
            </span>
          </div>
        </div>
      </div>

      {/* 手动触发优化 */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Zap className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold text-gray-800">手动触发优化</h2>
        </div>
        <div className="space-y-3">
          {devices.map((device) => (
            <div key={device.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-800">{device.name}</p>
                <p className="text-sm text-gray-500">{device.ip_address}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleTriggerOptimization(device.id)}
                  disabled={loading}
                  className="btn btn-primary flex items-center gap-2 text-sm"
                >
                  <Play size={16} />
                  全面优化
                </button>
                <button
                  onClick={() => handleRouteOptimization(device.id)}
                  disabled={loading}
                  className="btn btn-secondary flex items-center gap-2 text-sm"
                >
                  路由优化
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 优化日志 */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <History className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold text-gray-800">优化日志</h2>
        </div>
        {logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无优化记录</div>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <div key={log.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm font-medium">
                      {getOptimizationTypeLabel(log.optimization_type)}
                    </span>
                    <span className={`font-medium ${getResultColor(log.result)}`}>
                      {log.result === 'success' ? '成功' : log.result === 'failed' ? '失败' : '-'}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                {log.reason && (
                  <p className="text-sm text-gray-600 mb-2">原因: {log.reason}</p>
                )}
                {log.device_id && (
                  <p className="text-sm text-gray-500">设备ID: {log.device_id}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Optimization
