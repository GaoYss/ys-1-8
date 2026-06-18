from datetime import date

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ingredient, IngredientBatch, StockRecord

records_bp = Blueprint("records", __name__)


@records_bp.get("")
def list_records():
    record_type = request.args.get("type", "").strip()
    query = StockRecord.query
    if record_type:
        query = query.filter_by(record_type=record_type)
    records = query.order_by(StockRecord.created_at.desc()).all()
    return jsonify([record.to_dict() for record in records])


@records_bp.post("")
def create_record():
    data = request.get_json() or {}
    ingredient = Ingredient.query.get_or_404(data["ingredientId"])
    quantity = float(data["quantity"])
    record_type = data["recordType"]

    if record_type == "in":
        return _handle_stock_in(ingredient, quantity, data)
    elif record_type == "out":
        return _handle_stock_out(ingredient, quantity, data)
    else:
        return {"message": "recordType 必须是 in 或 out"}, 400


def _handle_stock_in(ingredient, quantity, data):
    batch_no = (data.get("batchNo") or "").strip()
    expiry_date_str = data.get("expiryDate")

    if not batch_no:
        return {"message": "入库必须填写批次号"}, 400
    if not expiry_date_str:
        return {"message": "入库必须填写保质期"}, 400

    try:
        expiry_date = date.fromisoformat(expiry_date_str)
    except (ValueError, TypeError):
        return {"message": "保质期格式错误，请使用 YYYY-MM-DD"}, 400

    if expiry_date <= date.today():
        return {"message": "保质期必须大于今天"}, 400

    existing = IngredientBatch.query.filter_by(
        ingredient_id=ingredient.id, batch_no=batch_no
    ).first()
    if existing:
        return {"message": "该原料已存在相同批次号"}, 400

    batch = IngredientBatch(
        ingredient_id=ingredient.id,
        batch_no=batch_no,
        quantity=quantity,
        remaining=quantity,
        expiry_date=expiry_date,
    )
    db.session.add(batch)
    db.session.flush()

    ingredient.stock += quantity

    record = StockRecord(
        ingredient_id=ingredient.id,
        batch_id=batch.id,
        record_type="in",
        quantity=quantity,
        operator=data.get("operator", "系统管理员"),
        source=data.get("source"),
        note=data.get("note"),
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict(), 201


def _handle_stock_out(ingredient, quantity, data):
    available_batches = (
        IngredientBatch.query.filter(
            IngredientBatch.ingredient_id == ingredient.id,
            IngredientBatch.remaining > 0,
        )
        .order_by(IngredientBatch.expiry_date.asc())
        .all()
    )

    valid_batches = [b for b in available_batches if not b.is_expired]
    valid_quantity = sum(b.remaining for b in valid_batches)

    if valid_quantity < quantity:
        expired_quantity = sum(b.remaining for b in available_batches if b.is_expired)
        if expired_quantity > 0:
            return {
                "message": f"可出库数量不足。可用{valid_quantity}{ingredient.unit}，另有{expired_quantity}{ingredient.unit}已过期无法出库"
            }, 400
        return {"message": "库存不足，无法出库"}, 400

    remaining_to_deduct = quantity
    used_batches = []
    records = []

    for batch in valid_batches:
        if remaining_to_deduct <= 0:
            break
        deduct = min(batch.remaining, remaining_to_deduct)
        batch.remaining -= deduct
        remaining_to_deduct -= deduct
        used_batches.append({"batch": batch, "deduct": deduct})

    ingredient.stock -= quantity

    for item in used_batches:
        record = StockRecord(
            ingredient_id=ingredient.id,
            batch_id=item["batch"].id,
            record_type="out",
            quantity=item["deduct"],
            operator=data.get("operator", "系统管理员"),
            source=data.get("source"),
            note=data.get("note"),
        )
        db.session.add(record)
        records.append(record)

    db.session.commit()

    if len(records) == 1:
        return records[0].to_dict(), 201
    return jsonify([r.to_dict() for r in records]), 201
