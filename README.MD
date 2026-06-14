# 奶茶原料采购系统

基于 Flask + Vue 的奶茶门店原料采购系统，包含原料库存预警、采购订单管理、供应商管理、入库出库记录。项目采用前后端分离结构，后端按模型和蓝图拆分，前端按路由页面、组件、API 客户端拆分。

## 功能模块

- 工作台：展示原料种类、预警数量、供应商数量、采购订单数量。
- 原料库存预警：维护原料、库存、单位、预警线、默认供应商，并支持只看预警原料。
- 采购订单管理：创建采购订单、添加订单明细、更新订单状态。
- 供应商管理：维护供应商联系人、电话、地址、评级和状态。
- 入库出库记录：登记原料入库和出库，出库时自动校验库存是否充足。

## 项目结构

```text
.
├── backend
│   ├── app
│   │   ├── models        # SQLAlchemy 数据模型
│   │   ├── routes        # Flask Blueprint API
│   │   ├── config.py
│   │   ├── extensions.py
│   │   └── seed.py       # 初始化演示数据
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── frontend
│   ├── src
│   │   ├── api           # axios API 客户端
│   │   ├── components    # 通用组件
│   │   ├── router        # Vue Router
│   │   ├── styles
│   │   ├── utils
│   │   └── views         # 业务页面
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docker-compose.yml
```

## Docker 启动

```bash
docker compose up --build -d
```

启动后访问：

- 前端：http://localhost:8080
- 后端健康检查：http://localhost:18050/api/health

停止服务：

```bash
docker compose down
```

如需清空 SQLite 数据卷：

```bash
docker compose down -v
```

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

前端开发服务默认运行在 http://localhost:5173，并通过 Vite 代理访问 http://localhost:5000/api。

## 主要 API

- `GET /api/health`：服务健康检查。
- `GET /api/inventory`：原料列表，支持 `keyword` 和 `warning=true` 查询。
- `POST /api/inventory`：新增原料。
- `GET /api/orders`：采购订单列表。
- `POST /api/orders`：创建采购订单。
- `PUT /api/orders/<id>/status`：更新订单状态。
- `GET /api/suppliers`：供应商列表。
- `POST /api/suppliers`：新增供应商。
- `GET /api/records`：出入库记录列表。
- `POST /api/records`：登记入库或出库。
