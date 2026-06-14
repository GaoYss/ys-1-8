from datetime import date

from .extensions import db
from .models import Ingredient, PurchaseOrder, PurchaseOrderItem, StockRecord, Supplier


def seed_data():
    if Supplier.query.first():
        return

    suppliers = [
        Supplier(
            name="香叶原料供应链",
            contact="林经理",
            phone="13800010001",
            address="杭州市余杭区良渚仓配园",
            rating=5,
        ),
        Supplier(
            name="甜蜜乳品配送",
            contact="周主管",
            phone="13800010002",
            address="上海市闵行区冷链中心",
            rating=4,
        ),
        Supplier(
            name="果然鲜果业",
            contact="陈女士",
            phone="13800010003",
            address="广州市白云区水果批发市场",
            rating=4,
        ),
    ]
    db.session.add_all(suppliers)
    db.session.flush()

    ingredients = [
        Ingredient(
            name="阿萨姆红茶",
            category="茶叶",
            unit="kg",
            stock=28,
            warning_threshold=20,
            supplier_id=suppliers[0].id,
        ),
        Ingredient(
            name="茉莉绿茶",
            category="茶叶",
            unit="kg",
            stock=12,
            warning_threshold=18,
            supplier_id=suppliers[0].id,
        ),
        Ingredient(
            name="鲜牛奶",
            category="乳制品",
            unit="L",
            stock=65,
            warning_threshold=50,
            supplier_id=suppliers[1].id,
        ),
        Ingredient(
            name="黑糖珍珠",
            category="小料",
            unit="kg",
            stock=9,
            warning_threshold=15,
            supplier_id=suppliers[1].id,
        ),
        Ingredient(
            name="芒果果浆",
            category="果浆",
            unit="瓶",
            stock=34,
            warning_threshold=24,
            supplier_id=suppliers[2].id,
        ),
    ]
    db.session.add_all(ingredients)
    db.session.flush()

    order = PurchaseOrder(
        order_no="PO20260611001",
        supplier_id=suppliers[0].id,
        status="approved",
        expected_date=date(2026, 6, 18),
        remark="补充茶叶安全库存",
    )
    order.items = [
        PurchaseOrderItem(
            ingredient_id=ingredients[0].id,
            quantity=30,
            unit_price=46,
        ),
        PurchaseOrderItem(
            ingredient_id=ingredients[1].id,
            quantity=25,
            unit_price=52,
        ),
    ]
    db.session.add(order)

    db.session.add_all(
        [
            StockRecord(
                ingredient_id=ingredients[2].id,
                record_type="in",
                quantity=40,
                operator="王店长",
                source="采购入库",
                note="每日乳品补货",
            ),
            StockRecord(
                ingredient_id=ingredients[3].id,
                record_type="out",
                quantity=6,
                operator="李班长",
                source="门店领用",
                note="晚班备料",
            ),
        ]
    )
    db.session.commit()
