import { useState, useEffect } from 'react'
import { monitoringAPI, devicesAPI } from '../api'
import { Activity, Cpu, HardDrive, Network, Clock } from 'lucide-react'

const Monitoring = () => {
  const [devices, setDevices] = useState<any[]>([])
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null)
  const [metrics, setMetrics] = useState<any>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDevices()
  }, [])

  useEffect(() => {
    if (selectedDevice) {
      loadMetrics(selectedDevice)
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

  const loadMetrics = async (deviceId: number) => {
    setLoading(true)
    try {
      const response = await monitoringAPI.getLatestMetrics(deviceId)
      setMetrics(response.data)
    } catch (error) {
      console.error('加载指标失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    if (selectedDevice) {
      await monitoringAPI.refreshMetrics(selectedDevice)
      loadMetrics(selectedDevice)
    }
  }

  const getMetricColor = (value: number, type: string) => {
    const thresholds: Record<string, number> = {
      cpu: 80,
      memory: 85,
      bandwidth: 90,
    }
    const threshold = thresholds[type] || 90
    if (value > threshold) return 'text-red-600'
    if (value > threshold * 0.8) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">监控</h1>
          <p className="text-gray-600 mt-1">设备性能监控</p>
        </div>
        <button onClick={handleRefresh} className="btn btn-primary flex items-center gap-2">
          <Activity size={20} />
          刷新
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

      {/* 指标卡片 */}
      {loading ? (
        <div className="text-center py-8">加载中...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <Cpu className="text-blue-600" size={24} />
              <h3 className="font-medium text-gray-700">CPU使用率</h3>
            </div>
            <p className={`text-3xl font-bold ${getMetricColor(metrics.cpu?.value || 0, 'cpu')}`}>
              {metrics.cpu?.value || 0}%
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {metrics.cpu?.timestamp ? new Date(metrics.cpu.timestamp).toLocaleString() : '-'}
            </p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <HardDrive className="text-green-600" size={24} />
              <h3 className="font-medium text-gray-700">内存使用率</h3>
            </div>
            <p className={`text-3xl font-bold ${getMetricColor(metrics.memory?.value || 0, 'memory')}`}>
              {metrics.memory?.value || 0}%
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {metrics.memory?.timestamp ? new Date(metrics.memory.timestamp).toLocaleString() : '-'}
            </p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <Network className="text-purple-600" size={24} />
              <h3 className="font-medium text-gray-700">带宽使用率</h3>
            </div>
            <p className={`text-3xl font-bold ${getMetricColor(metrics.bandwidth?.value || 0, 'bandwidth')}`}>
              {metrics.bandwidth?.value || 0}%
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {metrics.bandwidth?.timestamp ? new Date(metrics.bandwidth.timestamp).toLocaleString() : '-'}
            </p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <Clock className="text-orange-600" size={24} />
              <h3 className="font-medium text-gray-700">网络延迟</h3>
            </div>
            <p className="text-3xl font-bold text-gray-800">
              {metrics.latency?.value || 0}ms
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {metrics.latency?.timestamp ? new Date(metrics.latency.timestamp).toLocaleString() : '-'}
            </p>
          </div>
        </div>
      )}

      {/* 提示信息 */}
      <div className="card bg-blue-50 border border-blue-200">
        <div className="flex items-start gap-3">
          <Activity className="text-blue-600 mt-1" size={20} />
          <div>
            <h3 className="font-medium text-blue-800">监控说明</h3>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• CPU使用率超过80%将触发告警</li>
              <li>• 内存使用率超过85%将触发告警</li>
              <li>• 带宽使用率超过90%将触发告警</li>
              <li>• 网络延迟超过100ms将触发告警</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Monitoring
