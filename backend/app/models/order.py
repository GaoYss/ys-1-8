from datetime import datetime

from ..extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(40), nullable=False, unique=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="draft")
    expected_date = db.Column(db.Date, nullable=True)
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="orders")
    items = db.relationship(
        "PurchaseOrderItem", cascade="all, delete-orphan", back_populates="order"
    )

    @property
    def total_amount(self):
        return sum(item.quantity * item.unit_price for item in self.items)

    def to_dict(self):
        return {
            "id": self.id,
            "orderNo": self.order_no,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "status": self.status,
            "expectedDate": self.expected_date.isoformat() if self.expected_date else None,
            "remark": self.remark,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "totalAmount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
        }


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    order = db.relationship("PurchaseOrder", back_populates="items")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "unit": self.ingredient.unit if self.ingredient else None,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "amount": self.quantity * self.unit_price,
        }
