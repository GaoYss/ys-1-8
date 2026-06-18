<template>
  <section>
    <PageHeader eyebrow="Inventory" title="原料库存预警">
      <button v-if="editId" class="secondary-btn" @click="resetForm">取消编辑</button>
      <button class="primary-btn" @click="submitIngredient">{{ editId ? '更新原料' : '保存原料' }}</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          原料名称
          <input v-model="form.name" placeholder="如：椰果" />
        </label>
        <label>
          分类
          <input v-model="form.category" placeholder="茶叶 / 小料 / 乳制品" />
        </label>
        <label>
          单位
          <input v-model="form.unit" placeholder="kg / L / 瓶" />
        </label>
        <template v-if="!editId">
          <label>
            初始库存
            <input v-model.number="form.stock" type="number" min="0" step="0.01" />
          </label>
          <label>
            初始批次号（可选）
            <input v-model="form.batchNo" placeholder="不填则自动生成" />
          </label>
          <label>
            初始保质期（可选）
            <input v-model="form.expiryDate" type="date" />
          </label>
        </template>
        <template v-else>
          <label>
            当前库存（需通过出入库调整）
            <input :value="`${form.stock} ${form.unit || ''}`" disabled class="readonly-input" />
          </label>
          <label>
            批次总数
            <input :value="currentBatchCount + ' 个批次（剩余合计 = 库存）'" disabled class="readonly-input" />
          </label>
          <div></div>
        </template>
        <label>
          预警线
          <input v-model.number="form.warningThreshold" type="number" min="0" step="0.01" />
        </label>
        <label>
          默认供应商
          <select v-model.number="form.supplierId">
            <option :value="null">未指定</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
              {{ supplier.name }}
            </option>
          </select>
        </label>
      </div>
      <p v-if="formMessage" class="success-text">{{ formMessage }}</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <div class="toolbar">
      <input v-model="keyword" placeholder="搜索原料" @input="loadInventory" />
      <label class="checkbox-line">
        <input v-model="onlyWarning" type="checkbox" @change="loadInventory" />
        只看预警
      </label>
      <label class="checkbox-line">
        <input v-model="onlyBatchIssue" type="checkbox" @change="loadInventory" />
        只看临期/过期
      </label>
    </div>

    <DataTable :columns="columns" :rows="filteredInventory" @row:click="selectIngredient">
      <template #stock="{ row }">{{ row.stock }} {{ row.unit }}</template>
      <template #warningThreshold="{ row }">{{ row.warningThreshold }} {{ row.unit }}</template>
      <template #warning="{ row }">
        <StatusBadge
          :label="row.warning ? '库存预警' : '正常'"
          :variant="row.warning ? 'danger' : 'success'"
        />
      </template>
      <template #batchStatus="{ row }">
        <div class="batch-status-group">
          <StatusBadge
            v-if="row.expiringCount > 0"
            :label="`临期 ${row.expiringCount}`"
            variant="warning"
          />
          <StatusBadge
            v-if="row.expiredCount > 0"
            :label="`过期 ${row.expiredCount}`"
            variant="danger"
          />
          <span v-if="!row.expiringCount && !row.expiredCount" class="muted">-</span>
        </div>
      </template>
      <template #actions="{ row }">
        <button class="link-btn" @click.stop="editIngredient(row)">编辑</button>
      </template>
    </DataTable>

    <section v-if="selectedIngredient" class="panel batch-detail-panel">
      <div class="panel-header">
        <h2>{{ selectedIngredient.name }} - 批次详情</h2>
        <button class="secondary-btn" @click="selectedIngredient = null">关闭</button>
      </div>
      <DataTable :columns="batchColumns" :rows="selectedIngredient.batches || []">
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
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import {
  batchStatusText,
  batchStatusVariant,
  daysToExpiryText,
  formatDate
} from '../utils/format'

const inventory = ref([])
const suppliers = ref([])
const keyword = ref('')
const onlyWarning = ref(false)
const onlyBatchIssue = ref(false)
const selectedIngredient = ref(null)
const editId = ref(null)
const currentBatchCount = ref(0)
const error = ref('')
const formMessage = ref('')
const form = reactive({
  name: '',
  category: '',
  unit: '',
  stock: 0,
  warningThreshold: 0,
  supplierId: null,
  batchNo: '',
  expiryDate: ''
})

const columns = [
  { key: 'name', label: '原料' },
  { key: 'category', label: '分类' },
  { key: 'stock', label: '库存' },
  { key: 'warningThreshold', label: '预警线' },
  { key: 'supplierName', label: '供应商' },
  { key: 'warning', label: '库存状态' },
  { key: 'batchStatus', label: '批次状态' },
  { key: 'actions', label: '操作' }
]
const batchColumns = [
  { key: 'batchNo', label: '批次号' },
  { key: 'remaining', label: '剩余数量' },
  { key: 'expiryDate', label: '保质期' },
  { key: 'daysToExpiry', label: '距到期' },
  { key: 'status', label: '状态' }
]

const filteredInventory = computed(() => {
  let list = inventory.value
  if (onlyBatchIssue.value) {
    list = list.filter((item) => item.expiringCount > 0 || item.expiredCount > 0)
  }
  return list
})

function resetForm() {
  editId.value = null
  currentBatchCount.value = 0
  Object.assign(form, {
    name: '',
    category: '',
    unit: '',
    stock: 0,
    warningThreshold: 0,
    supplierId: null,
    batchNo: '',
    expiryDate: ''
  })
  error.value = ''
  formMessage.value = ''
}

function showFormMessage(msg) {
  formMessage.value = msg
  error.value = ''
  setTimeout(() => { formMessage.value = '' }, 3000)
}

async function loadInventory() {
  const res = await inventoryApi.list({
    keyword: keyword.value || undefined,
    warning: onlyWarning.value ? 'true' : undefined,
    includeBatches: 'true'
  })
  inventory.value = res.data
}

async function loadOptions() {
  const res = await inventoryApi.options()
  suppliers.value = res.data.suppliers
}

async function selectIngredient(row) {
  if (selectedIngredient.value?.id === row.id) {
    selectedIngredient.value = null
    return
  }
  if (row.batches && row.batches.length) {
    selectedIngredient.value = row
  } else {
    const res = await inventoryApi.get(row.id)
    selectedIngredient.value = res.data
  }
}

async function editIngredient(row) {
  const res = await inventoryApi.get(row.id)
  const data = res.data
  editId.value = data.id
  currentBatchCount.value = (data.batches || []).length
  Object.assign(form, {
    name: data.name,
    category: data.category,
    unit: data.unit,
    stock: data.stock,
    warningThreshold: data.warningThreshold,
    supplierId: data.supplierId,
    batchNo: '',
    expiryDate: ''
  })
  error.value = ''
  formMessage.value = ''
  selectedIngredient.value = null
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function submitIngredient() {
  error.value = ''
  formMessage.value = ''
  try {
    if (!form.name || !String(form.name).trim()) {
      error.value = '请填写原料名称'
      return
    }
    if (!form.category || !String(form.category).trim()) {
      error.value = '请填写分类'
      return
    }
    if (!form.unit || !String(form.unit).trim()) {
      error.value = '请填写单位'
      return
    }
    if (editId.value) {
      const payload = {
        name: form.name,
        category: form.category,
        unit: form.unit,
        warningThreshold: Number(form.warningThreshold) || 0,
        supplierId: form.supplierId
      }
      const res = await inventoryApi.update(editId.value, payload)
      const data = res.data
      currentBatchCount.value = (data.batches || []).length
      form.stock = data.stock
      showFormMessage('原料信息更新成功，库存保持不变。出入库请在"入库出库记录"中操作。')
    } else {
      const payload = {
        name: form.name,
        category: form.category,
        unit: form.unit,
        stock: Number(form.stock) || 0,
        warningThreshold: Number(form.warningThreshold) || 0,
        supplierId: form.supplierId,
        batchNo: form.batchNo || undefined,
        expiryDate: form.expiryDate || undefined
      }
      await inventoryApi.create(payload)
      try {
        localStorage.setItem('inventory_dashboard_stale', String(Date.now()))
      } catch (_) {}
      showFormMessage('原料创建成功！初始库存已自动生成初始批次。')
      resetForm()
    }
    await loadInventory()
  } catch (err) {
    error.value = err?.response?.data?.message || '保存失败，请检查输入'
  }
}

onMounted(async () => {
  await Promise.all([loadInventory(), loadOptions()])
})
</script>

<style scoped>
.muted {
  color: #a0aba4;
}
.batch-status-group {
  display: flex;
  gap: 6px;
}
.batch-detail-panel {
  margin-top: 18px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-header h2 {
  margin: 0;
}
tbody tr {
  cursor: pointer;
}
.link-btn {
  background: none;
  border: none;
  color: #1d6b53;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 6px;
  text-decoration: underline;
}
.link-btn:hover {
  opacity: 0.8;
}
.readonly-input {
  background: #f5f7f5;
  color: #546358;
}
.success-text {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
  border-radius: 6px;
  color: #2e7d32;
  font-size: 14px;
  margin: 12px 0 0;
  padding: 10px 14px;
}
</style>
