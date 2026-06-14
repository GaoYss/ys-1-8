<template>
  <section>
    <PageHeader eyebrow="Dashboard" title="采购与库存工作台" />

    <div class="metrics-grid">
      <article class="metric">
        <span>原料种类</span>
        <strong>{{ summary.ingredientCount }}</strong>
      </article>
      <article class="metric">
        <span>预警原料</span>
        <strong>{{ summary.warningCount }}</strong>
      </article>
      <article class="metric">
        <span>供应商</span>
        <strong>{{ suppliers.length }}</strong>
      </article>
      <article class="metric">
        <span>采购订单</span>
        <strong>{{ orders.length }}</strong>
      </article>
    </div>

    <div class="content-grid">
      <section class="panel">
        <h2>库存预警</h2>
        <DataTable :columns="warningColumns" :rows="warningItems">
          <template #stock="{ row }">
            {{ row.stock }} {{ row.unit }}
          </template>
          <template #warningThreshold="{ row }">
            {{ row.warningThreshold }} {{ row.unit }}
          </template>
        </DataTable>
      </section>
      <section class="panel">
        <h2>近期采购订单</h2>
        <DataTable :columns="orderColumns" :rows="orders.slice(0, 5)">
          <template #status="{ row }">
            <StatusBadge :label="statusText(row.status)" :variant="row.status" />
          </template>
          <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
        </DataTable>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { ordersApi } from '../api/orders'
import { suppliersApi } from '../api/suppliers'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { statusText } from '../utils/format'

const summary = ref({ ingredientCount: 0, warningCount: 0, totalStock: 0 })
const inventory = ref([])
const orders = ref([])
const suppliers = ref([])

const warningItems = computed(() => inventory.value.filter((item) => item.warning))
const warningColumns = [
  { key: 'name', label: '原料' },
  { key: 'stock', label: '当前库存' },
  { key: 'warningThreshold', label: '预警线' }
]
const orderColumns = [
  { key: 'orderNo', label: '订单号' },
  { key: 'supplierName', label: '供应商' },
  { key: 'status', label: '状态' },
  { key: 'totalAmount', label: '金额' }
]

onMounted(async () => {
  const [summaryRes, inventoryRes, ordersRes, suppliersRes] = await Promise.all([
    inventoryApi.summary(),
    inventoryApi.list(),
    ordersApi.list(),
    suppliersApi.list()
  ])
  summary.value = summaryRes.data
  inventory.value = inventoryRes.data
  orders.value = ordersRes.data
  suppliers.value = suppliersRes.data
})
</script>
