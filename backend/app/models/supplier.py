from datetime import datetime

from ..extensions import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    contact = db.Column(db.String(40), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(160), nullable=True)
    rating = db.Column(db.Integer, nullable=False, default=5)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredients = db.relationship("Ingredient", back_populates="supplier")
    orders = db.relationship("PurchaseOrder", back_populates="supplier")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "phone": self.phone,
            "address": self.address,
            "rating": self.rating,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
