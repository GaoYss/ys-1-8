import os
import sys
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import date, timedelta

os.environ["PYTHONIOENCODING"] = "utf-8"

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def record(name, ok, detail=""):
    tag = PASS if ok else FAIL
    line = f"{tag} {name}"
    if detail:
        line += f" -- {detail}"
    results.append((ok, line))
    print(line)

def create_legacy_database(db_path):
    """创建旧版本数据库：无 ingredient_batches 表，stock_records 无 batch_id"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE suppliers (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(80) NOT NULL UNIQUE,
            contact VARCHAR(40),
            phone VARCHAR(20),
            address VARCHAR(255),
            rating INTEGER DEFAULT 0,
            created_at DATETIME
        )
    """)

    c.execute("""
        CREATE TABLE ingredients (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(80) NOT NULL UNIQUE,
            category VARCHAR(40) NOT NULL,
            unit VARCHAR(20) NOT NULL,
            stock FLOAT NOT NULL DEFAULT 0,
            warning_threshold FLOAT NOT NULL DEFAULT 0,
            supplier_id INTEGER,
            updated_at DATETIME,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    c.execute("""
        CREATE TABLE stock_records (
            id INTEGER NOT NULL PRIMARY KEY,
            ingredient_id INTEGER NOT NULL,
            record_type VARCHAR(10) NOT NULL,
            quantity FLOAT NOT NULL,
            operator VARCHAR(40) NOT NULL,
            source VARCHAR(80),
            note VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)

    c.execute("""
        CREATE TABLE purchase_orders (
            id INTEGER NOT NULL PRIMARY KEY,
            order_no VARCHAR(40) NOT NULL UNIQUE,
            supplier_id INTEGER,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            total_amount FLOAT NOT NULL DEFAULT 0,
            expected_date DATE,
            remark VARCHAR(255),
            created_at DATETIME,
            updated_at DATETIME
        )
    """)

    c.execute("""
        CREATE TABLE purchase_order_items (
            id INTEGER NOT NULL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity FLOAT NOT NULL,
            unit_price FLOAT NOT NULL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES purchase_orders(id),
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)

    today = date.today().isoformat()
    c.execute(
        "INSERT INTO suppliers (id, name, contact, phone, address, rating) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "旧版本供应商A", "张老板", "13800001111", "旧地址", 4)
    )

    # 插入旧版原料数据，stock > 0 但没有批次表
    ingredients = [
        (1, "旧版阿萨姆红茶", "茶叶", "kg", 28.0, 20.0, 1),
        (2, "旧版茉莉绿茶", "茶叶", "kg", 12.0, 18.0, 1),
        (3, "旧版鲜牛奶", "乳制品", "L", 65.0, 50.0, 1),
        (4, "库存为0的原料", "测试", "kg", 0.0, 10.0, None),
    ]
    c.executemany(
        "INSERT INTO ingredients (id, name, category, unit, stock, warning_threshold, supplier_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ingredients
    )

    # 插入旧版出入库记录（没有 batch_id 列）
    old_records = [
        (1, 1, "in", 50.0, "旧系统入库员", "首次入库", "旧系统迁移前记录", today),
        (2, 1, "out", 22.0, "旧系统领用人", "门店领用", None, today),
    ]
    c.executemany(
        "INSERT INTO stock_records (id, ingredient_id, record_type, quantity, operator, source, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        old_records
    )

    conn.commit()
    conn.close()
    print(f"[Setup] 已创建旧版本数据库: {db_path}")
    print(f"[Setup] - 供应商: 1 个")
    print(f"[Setup] - 原料: {len(ingredients)} 个（其中库存非空: {sum(1 for i in ingredients if i[4]>0)}）")
    print(f"[Setup] - 出入库记录: {len(old_records)} 条（无 batch_id 列）")
    print(f"[Setup] - ingredient_batches 表: 不存在")
    print()


def main():
    tmpdir = tempfile.mkdtemp(prefix="legacy_db_test_")
    db_path = os.path.join(tmpdir, "legacy.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    try:
        # 1) 创建旧版数据库文件
        create_legacy_database(db_path)

        # 1.5) 验证旧数据库确实没有 ingredient_batches 表和 batch_id 列
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingredient_batches'")
        has_batches_table = c.fetchone() is not None
        record("旧数据库无 ingredient_batches 表", not has_batches_table,
               f"存在? {has_batches_table}")

        c.execute("PRAGMA table_info(stock_records)")
        cols = [row[1] for row in c.fetchall()]
        has_batch_id = "batch_id" in cols
        record("旧数据库 stock_records 无 batch_id 列", not has_batch_id,
               f"列: {cols}")
        conn.close()

        # 2) 启动 Flask 应用，触发自动迁移
        print("\n=== 启动 Flask 应用并触发迁移 ===")
        from app import create_app
        app = create_app()
        client = app.test_client()

        # 3) 验证迁移结果
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingredient_batches'")
        batches_table_created = c.fetchone() is not None
        record("迁移后创建了 ingredient_batches 表", batches_table_created)

        c.execute("PRAGMA table_info(stock_records)")
        cols = [row[1] for row in c.fetchall()]
        batch_id_added = "batch_id" in cols
        record("迁移后为 stock_records 添加了 batch_id 列", batch_id_added,
               f"当前列: {cols}")
        conn.close()

        # 4) 验证数据补齐：库存>0 的原料是否都有了批次
        r = client.get("/api/inventory?includeBatches=true")
        all_ings = r.get_json()
        print(f"\n=== 迁移后原料批次补齐情况 ({len(all_ings)} 个) ===")
        all_ok = True
        for ing in all_ings:
            batches = ing.get("batches") or []
            sum_remain = sum(b["remaining"] for b in batches)
            has_correct_batches = (ing["stock"] <= 0) or (len(batches) >= 1 and abs(ing["stock"] - sum_remain) < 0.001)
            if not has_correct_batches:
                all_ok = False
            detail = f"{ing['name']}: stock={ing['stock']}, batches={len(batches)}, sum_remain={sum_remain}"
            record(f"  {ing['name']}", has_correct_batches, detail)

        record("所有有库存的原料都有了批次且数量一致", all_ok)

        # 5) 验证旧记录可以被查询（无 batch_id 的记录也能返回，字段兼容）
        r = client.get("/api/records")
        records = r.get_json()
        old_record_ok = len(records) >= 2
        record(f"旧版本出入库记录可被读取 ({len(records)} 条)", old_record_ok)
        for rec in records:
            has_correct_fields = "batchNo" in rec and "ingredientName" in rec
            record(f"  记录[{rec['id']}] 字段兼容（含 batchNo 等新字段）", has_correct_fields,
                   f"batchNo={rec.get('batchNo')}")

        # 6) 迁移后执行入库：确保新流程可用
        print("\n=== 迁移后执行入库 ===")
        future = (date.today() + timedelta(days=60)).isoformat()
        payload = {
            "ingredientId": 1,
            "recordType": "in",
            "quantity": 30.0,
            "batchNo": "MIGRATION-TEST-IN-01",
            "expiryDate": future,
            "operator": "迁移测试员",
            "source": "入库验证",
        }
        r = client.post("/api/records", json=payload)
        record("迁移后入库成功 HTTP 201", r.status_code == 201,
               f"status={r.status_code}")
        data = r.get_json()
        record("入库返回 records 字段", isinstance(data, dict) and "records" in data)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ingredient_batches WHERE ingredient_id=1")
        batch_count = c.fetchone()[0]
        record("入库后创建了新批次", batch_count >= 2,
               f"batches for id=1: {batch_count}")
        conn.close()

        # 7) 迁移后执行出库：确保新流程可用
        print("\n=== 迁移后执行出库 ===")
        payload = {
            "ingredientId": 1,
            "recordType": "out",
            "quantity": 10.0,
            "operator": "迁移测试员",
            "source": "出库验证",
        }
        r = client.post("/api/records", json=payload)
        ok = r.status_code == 201
        data = r.get_json()
        record(f"迁移后出库成功 HTTP 201", ok,
               f"status={r.status_code}, data={json.dumps(data, ensure_ascii=False)[:100]}")
        r_summary = client.get("/api/inventory/summary")
        summary = r_summary.get_json()
        record("汇总接口可用（含临期/过期批次统计）",
               "expiringBatchCount" in summary and "expiredBatchCount" in summary,
               f"summary keys: {list(summary.keys())}")
        print(f"  summary: {summary}")

        # 8) 最终一致性验证
        print("\n=== 迁移后全局一致性 ===")
        r = client.get("/api/inventory?includeBatches=true")
        all_ings = r.get_json()
        consistent = True
        for ing in all_ings:
            s = sum(b["remaining"] for b in (ing.get("batches") or []))
            if abs(ing["stock"] - s) > 0.001:
                consistent = False
                print(f"  [WARN] {ing['name']}: stock={ing['stock']} vs sum={s}")
        record("全局一致性（所有原料 stock=sum 批次剩余）", consistent)

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

    # 汇总
    print("\n" + "="*70)
    total = len(results)
    passed = sum(1 for ok, _ in results if ok)
    failed = total - passed
    print(f"汇总：共 {total} 项检查，通过 {passed}，失败 {failed}")
    print("="*70)
    if failed > 0:
        print("\n失败项：")
        for ok, line in results:
            if not ok:
                print(f"  {line}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
