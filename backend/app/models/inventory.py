from datetime import datetime

from ..extensions import db


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    category = db.Column(db.String(40), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    stock = db.Column(db.Float, nullable=False, default=0)
    warning_threshold = db.Column(db.Float, nullable=False, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="ingredients")

    @property
    def warning(self):
        return self.stock <= self.warning_threshold

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "stock": self.stock,
            "warningThreshold": self.warning_threshold,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "warning": self.warning,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
