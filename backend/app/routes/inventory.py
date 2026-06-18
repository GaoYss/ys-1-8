from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ingredient, IngredientBatch, Supplier

inventory_bp = Blueprint("inventory", __name__)


def _generate_initial_batch_no(ingredient_id):
    today_str = date.today().strftime("%Y%m%d")
    return f"INIT-{ingredient_id}-{today_str}"


def _create_initial_batch(ingredient, quantity, expiry_days=365):
    if quantity <= 0:
        return None
    expiry = date.today() + timedelta(days=expiry_days)
    batch_no = _generate_initial_batch_no(ingredient.id)
    suffix = 0
    while IngredientBatch.query.filter_by(
        ingredient_id=ingredient.id, batch_no=batch_no
    ).first():
        suffix += 1
        batch_no = f"{_generate_initial_batch_no(ingredient.id)}-{suffix}"
    batch = IngredientBatch(
        ingredient_id=ingredient.id,
        batch_no=batch_no,
        quantity=quantity,
        remaining=quantity,
        expiry_date=expiry,
    )
    db.session.add(batch)
    return batch


def _ensure_batch_consistency(ingredient):
    batches_total = sum(
        b.remaining for b in IngredientBatch.query.filter_by(ingredient_id=ingredient.id).all()
    )
    if abs(ingredient.stock - batches_total) > 0.001:
        if batches_total > 0:
            ingredient.stock = batches_total
        else:
            _create_initial_batch(ingredient, ingredient.stock)
            db.session.flush()


def fix_missing_batches_for_existing_ingredients():
    ingredients = Ingredient.query.all()
    fixed = 0
    for ing in ingredients:
        batches = IngredientBatch.query.filter_by(ingredient_id=ing.id).all()
        batches_total = sum(b.remaining for b in batches)
        if ing.stock > 0 and batches_total <= 0:
            _create_initial_batch(ing, ing.stock)
            fixed += 1
        elif abs(ing.stock - batches_total) > 0.001 and batches_total > 0:
            ing.stock = batches_total
            fixed += 1
    if fixed > 0:
        db.session.commit()
    return fixed


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
    initial_stock = float(data.get("stock", 0))
    ingredient = Ingredient(
        name=data["name"],
        category=data["category"],
        unit=data["unit"],
        stock=initial_stock,
        warning_threshold=float(data.get("warningThreshold", 0)),
        supplier_id=data.get("supplierId"),
    )
    db.session.add(ingredient)
    db.session.flush()

    if initial_stock > 0:
        expiry_date_str = data.get("expiryDate")
        if expiry_date_str:
            try:
                expiry_date = date.fromisoformat(expiry_date_str)
            except (ValueError, TypeError):
                expiry_date = date.today() + timedelta(days=365)
        else:
            expiry_date = date.today() + timedelta(days=365)
        batch_no = data.get("batchNo") or _generate_initial_batch_no(ingredient.id)
        suffix = 0
        final_batch_no = batch_no
        while IngredientBatch.query.filter_by(
            ingredient_id=ingredient.id, batch_no=final_batch_no
        ).first():
            suffix += 1
            final_batch_no = f"{batch_no}-{suffix}"
        batch = IngredientBatch(
            ingredient_id=ingredient.id,
            batch_no=final_batch_no,
            quantity=initial_stock,
            remaining=initial_stock,
            expiry_date=expiry_date,
        )
        db.session.add(batch)

    db.session.commit()
    return ingredient.to_dict(include_batches=True), 201


@inventory_bp.get("/<int:ingredient_id>")
def get_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    _ensure_batch_consistency(ingredient)
    db.session.commit()
    return ingredient.to_dict(include_batches=True)


@inventory_bp.put("/<int:ingredient_id>")
def update_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    data = request.get_json() or {}

    ingredient.name = data.get("name", ingredient.name)
    ingredient.category = data.get("category", ingredient.category)
    ingredient.unit = data.get("unit", ingredient.unit)
    ingredient.warning_threshold = float(
        data.get("warningThreshold", ingredient.warning_threshold)
    )
    ingredient.supplier_id = data.get("supplierId", ingredient.supplier_id)

    _ensure_batch_consistency(ingredient)

    db.session.commit()
    return ingredient.to_dict(include_batches=True)


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
    _ensure_batch_consistency(ingredient)
    db.session.commit()
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
