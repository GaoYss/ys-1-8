export function statusText(status) {
  const map = {
    draft: '草稿',
    approved: '已审批',
    received: '已到货',
    cancelled: '已取消'
  }
  return map[status] || status
}

export function batchStatusText(status) {
  const map = {
    normal: '正常',
    expiring: '临期',
    expired: '已过期'
  }
  return map[status] || status
}

export function batchStatusVariant(status) {
  const map = {
    normal: 'success',
    expiring: 'warning',
    expired: 'danger'
  }
  return map[status] || 'neutral'
}

export function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

export function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN')
}

export function daysToExpiryText(days) {
  if (days == null) return '-'
  if (days < 0) return `已过期${Math.abs(days)}天`
  if (days === 0) return '今天到期'
  return `剩余${days}天`
}
