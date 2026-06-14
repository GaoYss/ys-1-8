from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ingredient, StockRecord

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
        ingredient.stock += quantity
    elif record_type == "out":
        if ingredient.stock < quantity:
            return {"message": "库存不足，无法出库"}, 400
        ingredient.stock -= quantity
    else:
        return {"message": "recordType 必须是 in 或 out"}, 400

    record = StockRecord(
        ingredient_id=ingredient.id,
        record_type=record_type,
        quantity=quantity,
        operator=data.get("operator", "系统管理员"),
        source=data.get("source"),
        note=data.get("note"),
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict(), 201
