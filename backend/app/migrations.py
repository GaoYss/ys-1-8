from datetime import date, timedelta

from sqlalchemy import text

from .extensions import db


def _table_exists(table_name):
    result = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name}
    )
    return result.fetchone() is not None


def _get_current_columns(table_name):
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    return [row[1] for row in result.fetchall()]


def _column_exists(table_name, column_name):
    return column_name in _get_current_columns(table_name)


def _ensure_column(table_name, column_name, column_def, default_value=None):
    """
    确保表存在指定列，不存在则 ALTER TABLE ADD COLUMN。
    SQLite 的 ALTER COLUMN 不能指定 NOT NULL 约束，因此所有新增列都默认 nullable。
    可选地为已存在行填入一个默认值。
    """
    if not _table_exists(table_name):
        return False
    if _column_exists(table_name, column_name):
        return False
    sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
    try:
        db.session.execute(sql)
        db.session.commit()
        print(f"[DB Migration] Added column: {table_name}.{column_name}")
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if "duplicate column name" in msg:
            return False
        raise
    if default_value is not None:
        try:
            quoted_col = column_name
            if isinstance(default_value, str):
                literal = default_value.replace("'", "''")
                update_sql = text(
                    f"UPDATE {table_name} SET {quoted_col} = '{literal}' "
                    f"WHERE {quoted_col} IS NULL"
                )
            else:
                update_sql = text(
                    f"UPDATE {table_name} SET {quoted_col} = {default_value} "
                    f"WHERE {quoted_col} IS NULL"
                )
            db.session.execute(update_sql)
            db.session.commit()
        except Exception:
            db.session.rollback()
    return True


def _create_ingredient_batches_table():
    sql = text("""
        CREATE TABLE IF NOT EXISTS ingredient_batches (
            id INTEGER NOT NULL PRIMARY KEY,
            ingredient_id INTEGER NOT NULL,
            batch_no VARCHAR(80) NOT NULL,
            quantity FLOAT NOT NULL,
            remaining FLOAT NOT NULL,
            expiry_date DATE NOT NULL,
            created_at DATETIME,
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)
    db.session.execute(sql)
    try:
        index_sql = text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_ingredient_batch
            ON ingredient_batches(ingredient_id, batch_no)
        """)
        db.session.execute(index_sql)
    except Exception:
        pass
    db.session.commit()
    print("[DB Migration] Created table: ingredient_batches")


def _add_batch_id_column():
    return _ensure_column("stock_records", "batch_id", "INTEGER")


def _ensure_all_supplier_columns():
    count = 0
    if _ensure_column("suppliers", "status", "VARCHAR(20)", default_value="active"):
        count += 1
    if _ensure_column("suppliers", "created_at", "DATETIME"):
        count += 1
    return count


def _ensure_all_ingredient_columns():
    count = 0
    if _ensure_column("ingredients", "updated_at", "DATETIME"):
        count += 1
    return count


def _ensure_all_purchase_order_columns():
    count = 0
    if _ensure_column("purchase_orders", "updated_at", "DATETIME"):
        count += 1
    return count


def _generate_batch_no_for_migration(ingredient_id, seq):
    today_str = date.today().strftime("%Y%m%d")
    return f"MIGR-{ingredient_id}-{today_str}-{seq}"


def _backfill_batches_for_existing_ingredients():
    from .models import Ingredient, IngredientBatch

    ingredients = Ingredient.query.all()
    added = 0
    for ing in ingredients:
        batches = IngredientBatch.query.filter_by(ingredient_id=ing.id).all()
        total_remaining = sum(b.remaining for b in batches)
        diff = float(ing.stock) - total_remaining
        if diff > 0.0001:
            seq = len(batches) + 1
            batch_no = _generate_batch_no_for_migration(ing.id, seq)
            while IngredientBatch.query.filter_by(
                ingredient_id=ing.id, batch_no=batch_no
            ).first():
                seq += 1
                batch_no = _generate_batch_no_for_migration(ing.id, seq)
            batch = IngredientBatch(
                ingredient_id=ing.id,
                batch_no=batch_no,
                quantity=diff,
                remaining=diff,
                expiry_date=date.today() + timedelta(days=90),
            )
            db.session.add(batch)
            added += 1
    if added > 0:
        db.session.commit()
        print(f"[DB Migration] Backfilled {added} initial batches for existing ingredients")
    return added


def run_db_migrations():
    migrations_applied = 0

    if not _table_exists("ingredient_batches"):
        _create_ingredient_batches_table()
        migrations_applied += 1
    else:
        print("[DB Migration] Table 'ingredient_batches' already exists")

    if _add_batch_id_column():
        migrations_applied += 1
    else:
        print("[DB Migration] Column 'stock_records.batch_id' already exists")

    migrations_applied += _ensure_all_supplier_columns()
    migrations_applied += _ensure_all_ingredient_columns()
    migrations_applied += _ensure_all_purchase_order_columns()

    backfilled = _backfill_batches_for_existing_ingredients()
    if backfilled > 0:
        migrations_applied += 1

    if migrations_applied > 0:
        print(f"[DB Migration] Total: {migrations_applied} migration(s) applied")
    else:
        print("[DB Migration] Schema is up to date, no migrations needed")

    return migrations_applied
