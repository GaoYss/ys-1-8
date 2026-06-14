from datetime import date

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import PurchaseOrder, PurchaseOrderItem

orders_bp = Blueprint("orders", __name__)


@orders_bp.get("")
def list_orders():
    status = request.args.get("status", "").strip()
    query = PurchaseOrder.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@orders_bp.post("")
def create_order():
    data = request.get_json() or {}
    expected_date = data.get("expectedDate")
    order = PurchaseOrder(
        order_no=data["orderNo"],
        supplier_id=data["supplierId"],
        status=data.get("status", "draft"),
        expected_date=date.fromisoformat(expected_date) if expected_date else None,
        remark=data.get("remark"),
    )
    for item in data.get("items", []):
        order.items.append(
            PurchaseOrderItem(
                ingredient_id=item["ingredientId"],
                quantity=float(item["quantity"]),
                unit_price=float(item["unitPrice"]),
            )
        )
    db.session.add(order)
    db.session.commit()
    return order.to_dict(), 201


@orders_bp.put("/<int:order_id>/status")
def update_order_status(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    data = request.get_json() or {}
    order.status = data.get("status", order.status)
    db.session.commit()
    return order.to_dict()
