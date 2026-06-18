from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ingredient, IngredientBatch, Supplier

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.get("")
def list_ingredients():
    keyword = request.args.get("keyword", "").strip()
    warning = request.args.get("warning")
    include_batches = request.args.get("includeBatches", "false").lower() == "true"

    query = Ingredient.query
    if keyword:
        query = query.filter(Ingredient.name.contains(keyword))
    if warning == "true":
        query = query.filter(Ingredient.stock <= Ingredient.warning_threshold)

    ingredients = query.order_by(Ingredient.warning_threshold.desc(), Ingredient.name).all()
    return jsonify([item.to_dict(include_batches=include_batches) for item in ingredients])


@inventory_bp.get("/summary")
def inventory_summary():
    ingredients = Ingredient.query.all()
    warning_count = sum(1 for item in ingredients if item.warning)
    stock_value = sum(item.stock for item in ingredients)
    all_batches = IngredientBatch.query.all()
    expiring_count = sum(1 for b in all_batches if b.is_expiring and b.remaining > 0)
    expired_count = sum(1 for b in all_batches if b.is_expired and b.remaining > 0)
    return {
        "ingredientCount": len(ingredients),
        "warningCount": warning_count,
        "totalStock": stock_value,
        "expiringBatchCount": expiring_count,
        "expiredBatchCount": expired_count,
    }


@inventory_bp.post("")
def create_ingredient():
    data = request.get_json() or {}
    ingredient = Ingredient(
        name=data["name"],
        category=data["category"],
        unit=data["unit"],
        stock=float(data.get("stock", 0)),
        warning_threshold=float(data.get("warningThreshold", 0)),
        supplier_id=data.get("supplierId"),
    )
    db.session.add(ingredient)
    db.session.commit()
    return ingredient.to_dict(), 201


@inventory_bp.get("/<int:ingredient_id>")
def get_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    return ingredient.to_dict(include_batches=True)


@inventory_bp.put("/<int:ingredient_id>")
def update_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    data = request.get_json() or {}

    ingredient.name = data.get("name", ingredient.name)
    ingredient.category = data.get("category", ingredient.category)
    ingredient.unit = data.get("unit", ingredient.unit)
    ingredient.stock = float(data.get("stock", ingredient.stock))
    ingredient.warning_threshold = float(
        data.get("warningThreshold", ingredient.warning_threshold)
    )
    ingredient.supplier_id = data.get("supplierId", ingredient.supplier_id)

    db.session.commit()
    return ingredient.to_dict()


@inventory_bp.get("/options")
def ingredient_options():
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return {
        "ingredients": [item.to_dict() for item in ingredients],
        "suppliers": [item.to_dict() for item in suppliers],
    }


@inventory_bp.get("/<int:ingredient_id>/batches")
def list_ingredient_batches(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    status = request.args.get("status", "").strip()
    batches = sorted(
        [b for b in ingredient.batches if b.remaining > 0],
        key=lambda b: b.expiry_date,
    )
    if status:
        batches = [b for b in batches if b.status == status]
    return jsonify([b.to_dict() for b in batches])


@inventory_bp.get("/batches")
def list_all_batches():
    status = request.args.get("status", "").strip()
    query = IngredientBatch.query.filter(IngredientBatch.remaining > 0)
    batches = query.order_by(IngredientBatch.expiry_date.asc()).all()
    if status:
        batches = [b for b in batches if b.status == status]
    return jsonify([b.to_dict() for b in batches])


@inventory_bp.get("/batches/<int:batch_id>")
def get_batch(batch_id):
    batch = IngredientBatch.query.get_or_404(batch_id)
    return batch.to_dict()
