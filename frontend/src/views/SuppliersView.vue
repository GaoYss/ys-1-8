<template>
  <section>
    <PageHeader eyebrow="Suppliers" title="供应商管理">
      <button class="primary-btn" @click="submitSupplier">保存供应商</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          供应商名称
          <input v-model="form.name" />
        </label>
        <label>
          联系人
          <input v-model="form.contact" />
        </label>
        <label>
          电话
          <input v-model="form.phone" />
        </label>
        <label>
          评级
          <input v-model.number="form.rating" type="number" min="1" max="5" />
        </label>
        <label class="span-2">
          地址
          <input v-model="form.address" />
        </label>
      </div>
    </section>

    <DataTable :columns="columns" :rows="suppliers">
      <template #rating="{ row }">{{ '★'.repeat(row.rating) }}</template>
      <template #status="{ row }">
        <StatusBadge
          :label="row.status === 'active' ? '合作中' : '停用'"
          :variant="row.status === 'active' ? 'success' : 'neutral'"
        />
      </template>
    </DataTable>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { suppliersApi } from '../api/suppliers'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const suppliers = ref([])
const form = reactive({
  name: '',
  contact: '',
  phone: '',
  address: '',
  rating: 5,
  status: 'active'
})
const columns = [
  { key: 'name', label: '供应商' },
  { key: 'contact', label: '联系人' },
  { key: 'phone', label: '电话' },
  { key: 'rating', label: '评级' },
  { key: 'status', label: '状态' }
]

async function loadSuppliers() {
  const res = await suppliersApi.list()
  suppliers.value = res.data
}

async function submitSupplier() {
  await suppliersApi.create({ ...form })
  Object.assign(form, {
    name: '',
    contact: '',
    phone: '',
    address: '',
    rating: 5,
    status: 'active'
  })
  await loadSuppliers()
}

onMounted(loadSuppliers)
</script>
