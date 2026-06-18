from datetime import date, datetime

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
    batches = db.relationship(
        "IngredientBatch",
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )

    @property
    def warning(self):
        return self.stock <= self.warning_threshold

    @property
    def expiring_batches(self):
        return [
            b for b in self.batches if b.remaining > 0 and b.is_expiring
        ]

    @property
    def expired_batches(self):
        return [b for b in self.batches if b.remaining > 0 and b.is_expired]

    def to_dict(self, include_batches=False):
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "stock": self.stock,
            "warningThreshold": self.warning_threshold,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "warning": self.warning,
            "expiringCount": len(self.expiring_batches),
            "expiredCount": len(self.expired_batches),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_batches:
            active_batches = sorted(
                [b for b in self.batches if b.remaining > 0],
                key=lambda b: b.expiry_date,
            )
            data["batches"] = [b.to_dict() for b in active_batches]
        return data


class IngredientBatch(db.Model):
    __tablename__ = "ingredient_batches"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=False
    )
    batch_no = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    remaining = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient = db.relationship("Ingredient", back_populates="batches")

    __table_args__ = (
        db.UniqueConstraint("ingredient_id", "batch_no", name="uq_ingredient_batch"),
    )

    @property
    def days_to_expiry(self):
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self):
        return date.today() > self.expiry_date

    @property
    def is_expiring(self):
        days = self.days_to_expiry
        return 0 <= days <= 30

    @property
    def status(self):
        if self.is_expired:
            return "expired"
        if self.is_expiring:
            return "expiring"
        return "normal"

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "batchNo": self.batch_no,
            "quantity": self.quantity,
            "remaining": self.remaining,
            "unit": self.ingredient.unit if self.ingredient else None,
            "expiryDate": self.expiry_date.isoformat() if self.expiry_date else None,
            "daysToExpiry": self.days_to_expiry,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
