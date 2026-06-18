<template>
  <section>
    <PageHeader eyebrow="Stock Records" title="入库出库记录">
      <button class="primary-btn" @click="submitRecord">登记</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          原料
          <select v-model.number="form.ingredientId" @change="onIngredientChange">
            <option disabled :value="null">选择原料</option>
            <option v-for="item in ingredients" :key="item.id" :value="item.id">
              {{ item.name }} / 库存 {{ item.stock }} {{ item.unit }}
            </option>
          </select>
        </label>
        <label>
          类型
          <select v-model="form.recordType">
            <option value="in">入库</option>
            <option value="out">出库</option>
          </select>
        </label>
        <label>
          数量
          <input v-model.number="form.quantity" type="number" min="0.01" step="0.01" />
        </label>
        <template v-if="form.recordType === 'in'">
          <label>
            批次号
            <input v-model="form.batchNo" placeholder="如：ASM-20260618-01" />
          </label>
          <label>
            保质期
            <input v-model="form.expiryDate" type="date" />
          </label>
        </template>
        <label>
          经办人
          <input v-model="form.operator" />
        </label>
        <label>
          来源/用途
          <input v-model="form.source" />
        </label>
        <label class="span-2">
          备注
          <input v-model="form.note" />
        </label>
      </div>
    </section>

    <section v-if="form.recordType === 'out' && form.ingredientId && batches.length" class="panel">
      <h2>可用批次（按临期优先自动扣减）</h2>
      <p class="hint">系统将按照保质期从近到远（FEFO）自动扣减，已过期批次将无法出库。</p>
      <DataTable :columns="batchColumns" :rows="batches">
        <template #remaining="{ row }">{{ row.remaining }} {{ row.unit }}</template>
        <template #expiryDate="{ row }">{{ formatDate(row.expiryDate) }}</template>
        <template #daysToExpiry="{ row }">{{ daysToExpiryText(row.daysToExpiry) }}</template>
        <template #status="{ row }">
          <StatusBadge
            :label="batchStatusText(row.status)"
            :variant="batchStatusVariant(row.status)"
          />
        </template>
      </DataTable>
    </section>

    <div v-if="successMessage" class="success-text">{{ successMessage }}</div>
    <p v-if="error" class="error-text">{{ error }}</p>

    <DataTable :columns="columns" :rows="records">
      <template #recordType="{ row }">
        <StatusBadge
          :label="row.recordType === 'in' ? '入库' : '出库'"
          :variant="row.recordType === 'in' ? 'success' : 'warning'"
        />
      </template>
      <template #quantity="{ row }">{{ row.quantity }} {{ row.unit }}</template>
      <template #batchNo="{ row }">
        <span v-if="row.batchNo">{{ row.batchNo }}</span>
        <span v-else class="muted">-</span>
      </template>
      <template #expiryDate="{ row }">
        <span v-if="row.expiryDate">{{ formatDate(row.expiryDate) }}</span>
        <span v-else class="muted">-</span>
      </template>
      <template #createdAt="{ row }">{{ formatDateTime(row.createdAt) }}</template>
    </DataTable>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'

import { inventoryApi } from '../api/inventory'
import { recordsApi } from '../api/records'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import {
  batchStatusText,
  batchStatusVariant,
  daysToExpiryText,
  formatDate,
  formatDateTime
} from '../utils/format'

const records = ref([])
const ingredients = ref([])
const batches = ref([])
const error = ref('')
const successMessage = ref('')
const form = reactive({
  ingredientId: null,
  recordType: 'in',
  quantity: 1,
  batchNo: '',
  expiryDate: '',
  operator: '系统管理员',
  source: '',
  note: ''
})
const columns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'recordType', label: '类型' },
  { key: 'quantity', label: '数量' },
  { key: 'batchNo', label: '批次号' },
  { key: 'expiryDate', label: '保质期' },
  { key: 'operator', label: '经办人' },
  { key: 'source', label: '来源/用途' },
  { key: 'createdAt', label: '时间' }
]
const batchColumns = [
  { key: 'batchNo', label: '批次号' },
  { key: 'remaining', label: '剩余数量' },
  { key: 'expiryDate', label: '保质期' },
  { key: 'daysToExpiry', label: '距到期' },
  { key: 'status', label: '状态' }
]

function showSuccess(msg) {
  successMessage.value = msg
  error.value = ''
  setTimeout(() => { successMessage.value = '' }, 3500)
}

async function loadRecords() {
  const res = await recordsApi.list()
  records.value = res.data
}

async function loadOptions() {
  const res = await inventoryApi.options()
  ingredients.value = res.data.ingredients
}

async function loadBatches(ingredientId) {
  if (!ingredientId) {
    batches.value = []
    return
  }
  const res = await inventoryApi.listIngredientBatches(ingredientId)
  batches.value = res.data
}

function onIngredientChange() {
  loadBatches(form.ingredientId)
}

watch(
  () => form.recordType,
  () => {
    if (form.recordType === 'out') {
      loadBatches(form.ingredientId)
    } else {
      batches.value = []
    }
  }
)

async function submitRecord() {
  error.value = ''
  successMessage.value = ''
  try {
    if (form.ingredientId == null) {
      error.value = '请选择原料'
      return
    }
    if (!form.quantity || form.quantity <= 0) {
      error.value = '数量必须大于 0'
      return
    }
    const payload = { ...form }
    if (form.recordType === 'in') {
      if (!payload.batchNo || !String(payload.batchNo).trim()) {
        error.value = '请填写批次号'
        return
      }
      if (!payload.expiryDate) {
        error.value = '请选择保质期'
        return
      }
    } else {
      delete payload.batchNo
      delete payload.expiryDate
    }
    const res = await recordsApi.create(payload)
    const result = res.data
    const createdCount = (result.records || []).length
    const totalQty = result.totalQuantity || payload.quantity
    const unit = (result.records && result.records[0] && result.records[0].unit) || ''
    const actionText = payload.recordType === 'in' ? '入库' : '出库'
    const batchHint = createdCount > 1 ? `（拆分${createdCount}个批次）` : ''
    try {
      localStorage.setItem('inventory_dashboard_stale', String(Date.now()))
    } catch (_) {}
    showSuccess(`${actionText}成功：${totalQty}${unit} ${batchHint}`)
    Object.assign(form, {
      ingredientId: null,
      recordType: 'in',
      quantity: 1,
      batchNo: '',
      expiryDate: '',
      operator: '系统管理员',
      source: '',
      note: ''
    })
    batches.value = []
    await Promise.all([loadRecords(), loadOptions()])
  } catch (err) {
    error.value = err?.response?.data?.message || '登记失败，请检查输入'
  }
}

onMounted(async () => {
  await Promise.all([loadRecords(), loadOptions()])
})
</script>

<style scoped>
.hint {
  color: #6b786f;
  font-size: 13px;
  margin: 0 0 12px;
}
.muted {
  color: #a0aba4;
}
.success-text {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  border-radius: 6px;
  color: #2e7d32;
  font-size: 14px;
  margin: 8px 0 14px;
  padding: 10px 14px;
}
</style>
