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
    </div>

    <DataTable :columns="columns" :rows="inventory">
      <template #stock="{ row }">{{ row.stock }} {{ row.unit }}</template>
      <template #warningThreshold="{ row }">{{ row.warningThreshold }} {{ row.unit }}</template>
      <template #warning="{ row }">
        <StatusBadge
          :label="row.warning ? '库存预警' : '正常'"
          :variant="row.warning ? 'danger' : 'success'"
        />
      </template>
    </DataTable>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const inventory = ref([])
const suppliers = ref([])
const keyword = ref('')
const onlyWarning = ref(false)
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
  { key: 'warning', label: '状态' }
]

async function loadInventory() {
  const res = await inventoryApi.list({
    keyword: keyword.value || undefined,
    warning: onlyWarning.value ? 'true' : undefined
  })
  inventory.value = res.data
}

async function loadOptions() {
  const res = await inventoryApi.options()
  suppliers.value = res.data.suppliers
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
