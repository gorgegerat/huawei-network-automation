import { useState, useEffect } from 'react'
import { alertsAPI } from '../api'
import { AlertTriangle, Check, Filter } from 'lucide-react'

const Alerts = () => {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'resolved' | 'unresolved'>('unresolved')

  useEffect(() => {
    loadAlerts()
  }, [filter, statusFilter])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (filter !== 'all') params.severity = filter
      if (statusFilter !== 'all') params.is_resolved = statusFilter === 'resolved'
      
      const response = await alertsAPI.getAll(params)
      setAlerts(response.data)
    } catch (error) {
      console.error('加载告警失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async (alertId: number) => {
    try {
      await alertsAPI.resolve(alertId)
      loadAlerts()
    } catch (error) {
      alert('解决失败')
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-500'
      case 'warning':
        return 'bg-yellow-100 text-yellow-700 border-yellow-500'
      case 'info':
        return 'bg-blue-100 text-blue-700 border-blue-500'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-500'
    }
  }

  if (loading) {
    return <div className="text-center py-8">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">告警</h1>
        <p className="text-gray-600 mt-1">系统告警管理</p>
      </div>

      {/* 过滤器 */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-500" />
            <span className="text-sm font-medium text-gray-700">过滤:</span>
          </div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="input w-auto"
          >
            <option value="all">所有级别</option>
            <option value="critical">严重</option>
            <option value="warning">警告</option>
            <option value="info">信息</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="input w-auto"
          >
            <option value="unresolved">未解决</option>
            <option value="resolved">已解决</option>
            <option value="all">全部</option>
          </select>
        </div>
      </div>

      {/* 告警列表 */}
      <div className="card">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无告警</div>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border-l-4 ${getSeverityColor(alert.severity)} ${
                  alert.is_resolved ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <AlertTriangle size={20} />
                      <h3 className="font-medium text-gray-800">{alert.title}</h3>
                      {alert.is_resolved && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          已解决
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 mb-2">{alert.message}</p>
                    <p className="text-sm text-gray-500">
                      时间: {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!alert.is_resolved && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="btn btn-primary flex items-center gap-2 ml-4"
                    >
                      <Check size={18} />
                      解决
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Alerts
