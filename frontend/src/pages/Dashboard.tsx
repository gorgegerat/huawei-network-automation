import { useState, useEffect } from 'react'
import { devicesAPI, alertsAPI, monitoringAPI } from '../api'
import {
  Server,
  AlertTriangle,
  Activity,
  TrendingUp,
  CheckCircle,
  XCircle,
  StopCircle,
  Download
} from 'lucide-react'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalDevices: 0,
    onlineDevices: 0,
    offlineDevices: 0,
    totalAlerts: 0,
    criticalAlerts: 0,
  })
  const [recentAlerts, setRecentAlerts] = useState<any[]>([])
  const [monitoringStatus, setMonitoringStatus] = useState<any>(null)
  const [exporting, setExporting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [devicesRes, alertsRes, alertStats, monitorStatus] = await Promise.all([
        devicesAPI.getAll(),
        alertsAPI.getAll({ limit: 5 }),
        alertsAPI.getStats(),
        monitoringAPI.getStatus(),
      ])

      const devices = devicesRes.data
      const onlineCount = devices.filter((d: any) => d.status === 'online').length

      setStats({
        totalDevices: devices.length,
        onlineDevices: onlineCount,
        offlineDevices: devices.length - onlineCount,
        totalAlerts: alertStats.data.total,
        criticalAlerts: alertStats.data.critical,
      })

      setRecentAlerts(alertsRes.data)
      setMonitoringStatus(monitorStatus.data)
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleForceStopMonitoring = async () => {
    if (!confirm('确定要强制停止所有监控任务吗？')) return
    try {
      await monitoringAPI.forceStop()
      alert('监控任务已强制停止')
      loadDashboardData()
    } catch (error) {
      alert('强制停止失败')
    }
  }

  const handleExportMonitoringResults = async (format: string = 'excel') => {
    setExporting(true)
    try {
      const response = await monitoringAPI.exportResults({ format, hours: 24 })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `monitoring_results.${format === 'excel' ? 'xlsx' : 'csv'}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      alert('导出失败')
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">仪表盘</h1>
        <p className="text-gray-600 mt-1">系统概览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">设备总数</p>
              <p className="text-3xl font-bold text-gray-800 mt-1">{stats.totalDevices}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Server className="text-blue-600" size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">在线设备</p>
              <p className="text-3xl font-bold text-green-600 mt-1">{stats.onlineDevices}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">离线设备</p>
              <p className="text-3xl font-bold text-red-600 mt-1">{stats.offlineDevices}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <XCircle className="text-red-600" size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">告警总数</p>
              <p className="text-3xl font-bold text-orange-600 mt-1">{stats.totalAlerts}</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertTriangle className="text-orange-600" size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* 最近告警 */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-800 mb-4">最近告警</h2>
        {recentAlerts.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无告警</p>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : alert.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-800">{alert.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      alert.severity === 'critical'
                        ? 'bg-red-100 text-red-700'
                        : alert.severity === 'warning'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {alert.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 快捷操作 */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-800 mb-4">快捷操作</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <button className="p-4 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors text-left">
            <Activity className="text-primary-600 mb-2" size={24} />
            <p className="font-medium text-gray-800">刷新监控数据</p>
            <p className="text-sm text-gray-600">更新所有设备指标</p>
          </button>
          <button className="p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors text-left">
            <TrendingUp className="text-green-600 mb-2" size={24} />
            <p className="font-medium text-gray-800">触发自动优化</p>
            <p className="text-sm text-gray-600">优化网络配置</p>
          </button>
          <button className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors text-left">
            <Server className="text-blue-600 mb-2" size={24} />
            <p className="font-medium text-gray-800">扫描新设备</p>
            <p className="text-sm text-gray-600">发现并自动部署</p>
          </button>
          <button
            onClick={handleForceStopMonitoring}
            className="p-4 bg-red-50 hover:bg-red-100 rounded-lg transition-colors text-left"
          >
            <StopCircle className="text-red-600 mb-2" size={24} />
            <p className="font-medium text-gray-800">强制停止监控</p>
            <p className="text-sm text-gray-600">
              {monitoringStatus?.running ? '监控运行中' : '监控已停止'}
            </p>
          </button>
          <button
            onClick={() => handleExportMonitoringResults('excel')}
            disabled={exporting}
            className="p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors text-left disabled:opacity-50"
          >
            <Download className="text-purple-600 mb-2" size={24} />
            <p className="font-medium text-gray-800">导出监控结果</p>
            <p className="text-sm text-gray-600">
              {exporting ? '导出中...' : '下载Excel报表'}
            </p>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
