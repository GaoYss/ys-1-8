export function statusText(status) {
  const map = {
    draft: '草稿',
    approved: '已审批',
    received: '已到货',
    cancelled: '已取消'
  }
  return map[status] || status
}

export function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
