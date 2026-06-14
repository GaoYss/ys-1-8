<template>
  <section>
    <PageHeader eyebrow="Orders" title="采购订单管理">
      <button class="primary-btn" @click="submitOrder">创建订单</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          订单号
          <input v-model="form.orderNo" />
        </label>
        <label>
          供应商
          <select v-model.number="form.supplierId">
            <option disabled :value="null">选择供应商</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
              {{ supplier.name }}
            </option>
          </select>
        </label>
        <label>
          预计到货
          <input v-model="form.expectedDate" type="date" />
        </label>
        <label>
          备注
          <input v-model="form.remark" />
        </label>
      </div>

      <div class="line-editor">
        <select v-model.number="line.ingredientId">
          <option disabled :value="null">选择原料</option>
          <option v-for="item in ingredients" :key="item.id" :value="item.id">
            {{ item.name }} / {{ item.unit }}
          </option>
        </select>
        <input v-model.number="line.quantity" type="number" min="1" placeholder="数量" />
        <input v-model.number="line.unitPrice" type="number" min="0" placeholder="单价" />
        <button class="secondary-btn" @click="addLine">添加明细</button>
      </div>

      <DataTable :columns="lineColumns" :rows="form.items">
        <template #ingredientName="{ row }">{{ ingredientName(row.ingredientId) }}</template>
        <template #amount="{ row }">¥{{ (row.quantity * row.unitPrice).toFixed(2) }}</template>
      </DataTable>
    </section>

    <DataTable :columns="columns" :rows="orders">
      <template #status="{ row }">
        <select :value="row.status" @change="changeStatus(row, $event.target.value)">
          <option value="draft">草稿</option>
          <option value="approved">已审批</option>
          <option value="received">已到货</option>
          <option value="cancelled">已取消</option>
        </select>
      </template>
      <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
    </DataTable>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { ordersApi } from '../api/orders'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'

const orders = ref([])
const suppliers = ref([])
const ingredients = ref([])
const form = reactive({
  orderNo: `PO${new Date().toISOString().slice(0, 10).replaceAll('-', '')}001`,
  supplierId: null,
  expectedDate: '',
  remark: '',
  items: []
})
const line = reactive({ ingredientId: null, quantity: 1, unitPrice: 0 })

const columns = [
  { key: 'orderNo', label: '订单号' },
  { key: 'supplierName', label: '供应商' },
  { key: 'expectedDate', label: '预计到货' },
  { key: 'status', label: '状态' },
  { key: 'totalAmount', label: '金额' }
]
const lineColumns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'quantity', label: '数量' },
  { key: 'unitPrice', label: '单价' },
  { key: 'amount', label: '小计' }
]

function ingredientName(id) {
  return ingredients.value.find((item) => item.id === id)?.name || '-'
}

function addLine() {
  if (!line.ingredientId || !line.quantity) return
  form.items.push({ id: Date.now(), ...line })
  Object.assign(line, { ingredientId: null, quantity: 1, unitPrice: 0 })
}

async function loadOrders() {
  const res = await ordersApi.list()
  orders.value = res.data
}

async function submitOrder() {
  if (!form.supplierId || !form.items.length) return
  await ordersApi.create({ ...form })
  Object.assign(form, {
    orderNo: `PO${new Date().toISOString().slice(0, 10).replaceAll('-', '')}${Date.now()
      .toString()
      .slice(-3)}`,
    supplierId: null,
    expectedDate: '',
    remark: '',
    items: []
  })
  await loadOrders()
}

async function changeStatus(order, status) {
  await ordersApi.updateStatus(order.id, status)
  await loadOrders()
}

onMounted(async () => {
  const [optionsRes] = await Promise.all([inventoryApi.options(), loadOrders()])
  ingredients.value = optionsRes.data.ingredients
  suppliers.value = optionsRes.data.suppliers
})
</script>
