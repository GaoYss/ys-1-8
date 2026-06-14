<template>
  <section>
    <PageHeader eyebrow="Stock Records" title="入库出库记录">
      <button class="primary-btn" @click="submitRecord">登记</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          原料
          <select v-model.number="form.ingredientId">
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
          <input v-model.number="form.quantity" type="number" min="1" />
        </label>
        <label>
          经办人
          <input v-model="form.operator" />
        </label>
        <label>
          来源/用途
          <input v-model="form.source" />
        </label>
        <label>
          备注
          <input v-model="form.note" />
        </label>
      </div>
    </section>

    <p v-if="error" class="error-text">{{ error }}</p>

    <DataTable :columns="columns" :rows="records">
      <template #recordType="{ row }">
        <StatusBadge
          :label="row.recordType === 'in' ? '入库' : '出库'"
          :variant="row.recordType === 'in' ? 'success' : 'warning'"
        />
      </template>
      <template #quantity="{ row }">{{ row.quantity }} {{ row.unit }}</template>
      <template #createdAt="{ row }">{{ formatDateTime(row.createdAt) }}</template>
    </DataTable>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { recordsApi } from '../api/records'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDateTime } from '../utils/format'

const records = ref([])
const ingredients = ref([])
const error = ref('')
const form = reactive({
  ingredientId: null,
  recordType: 'in',
  quantity: 1,
  operator: '系统管理员',
  source: '',
  note: ''
})
const columns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'recordType', label: '类型' },
  { key: 'quantity', label: '数量' },
  { key: 'operator', label: '经办人' },
  { key: 'source', label: '来源/用途' },
  { key: 'createdAt', label: '时间' }
]

async function loadRecords() {
  const res = await recordsApi.list()
  records.value = res.data
}

async function loadOptions() {
  const res = await inventoryApi.options()
  ingredients.value = res.data.ingredients
}

async function submitRecord() {
  error.value = ''
  try {
    await recordsApi.create({ ...form })
    Object.assign(form, {
      ingredientId: null,
      recordType: 'in',
      quantity: 1,
      operator: '系统管理员',
      source: '',
      note: ''
    })
    await Promise.all([loadRecords(), loadOptions()])
  } catch (err) {
    error.value = err.response?.data?.message || '登记失败'
  }
}

onMounted(async () => {
  await Promise.all([loadRecords(), loadOptions()])
})
</script>
