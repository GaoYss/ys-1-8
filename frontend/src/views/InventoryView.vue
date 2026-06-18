<template>
  <section>
    <PageHeader eyebrow="Inventory" title="原料库存预警">
      <button class="primary-btn" @click="submitIngredient">保存原料</button>
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
        <label>
          当前库存
          <input v-model.number="form.stock" type="number" min="0" />
        </label>
        <label>
          预警线
          <input v-model.number="form.warningThreshold" type="number" min="0" />
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
const form = reactive({
  name: '',
  category: '',
  unit: '',
  stock: 0,
  warningThreshold: 0,
  supplierId: null
})

const columns = [
  { key: 'name', label: '原料' },
  { key: 'category', label: '分类' },
  { key: 'stock', label: '库存' },
  { key: 'warningThreshold', label: '预警线' },
  { key: 'supplierName', label: '供应商' },
  { key: 'warning', label: '库存状态' },
  { key: 'batchStatus', label: '批次状态' }
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

async function submitIngredient() {
  await inventoryApi.create({ ...form })
  Object.assign(form, {
    name: '',
    category: '',
    unit: '',
    stock: 0,
    warningThreshold: 0,
    supplierId: null
  })
  await loadInventory()
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
</style>
