from sqlalchemy import func

from models.ledger import MarketplaceOrder, RefundRecord, SellerBalance, SellerPayout
from models.product import Product
from utils.constants import USER_TYPE


class DashboardSerializer(object):
    def _base_summary(self):
        return {
            "orders_count": 0,
            "paid_orders_count": 0,
            "refunded_orders_count": 0,
            "gross_sales_amount": "0.00",
            "net_seller_amount": "0.00",
            "refunds_count": 0,
            "refunds_amount": "0.00",
            "products_count": 0,
            "payouts_count": 0,
            "payouts_paid_amount": "0.00",
            "available_for_payout": "0.00",
            "pending_payout": "0.00",
        }

    def _serialize_balance(self, seller_id):
        balance = SellerBalance.query.filter_by(seller_id=seller_id).first()
        if not balance:
            return "0.00", "0.00"
        return str(balance.available_for_payout or 0), str(balance.pending_payout or 0)

    def seller_summary(self, seller_id):
        summary = self._base_summary()
        orders_query = MarketplaceOrder.query.filter_by(seller_id=seller_id)
        summary["orders_count"] = orders_query.count()
        summary["paid_orders_count"] = orders_query.filter_by(payment_status="paid").count()
        summary["refunded_orders_count"] = orders_query.filter_by(payment_status="refunded").count()
        gross_sales = orders_query.with_entities(func.coalesce(func.sum(MarketplaceOrder.gross_amount), 0)).scalar() or 0
        net_sales = orders_query.with_entities(func.coalesce(func.sum(MarketplaceOrder.net_seller_amount), 0)).scalar() or 0
        refunds = RefundRecord.query.join(MarketplaceOrder).filter(MarketplaceOrder.seller_id == seller_id)
        refunds_amount = refunds.with_entities(func.coalesce(func.sum(RefundRecord.amount), 0)).scalar() or 0
        summary["gross_sales_amount"] = str(gross_sales)
        summary["net_seller_amount"] = str(net_sales)
        summary["refunds_count"] = refunds.count()
        summary["refunds_amount"] = str(refunds_amount)
        summary["products_count"] = Product.query.filter_by(owner_id=seller_id).count()
        summary["payouts_count"] = SellerPayout.query.filter_by(seller_id=seller_id).count()
        summary["payouts_paid_amount"] = str(
            SellerPayout.query.filter_by(seller_id=seller_id, status="paid")
            .with_entities(func.coalesce(func.sum(SellerPayout.amount), 0))
            .scalar()
            or 0
        )
        available, pending = self._serialize_balance(seller_id)
        summary["available_for_payout"] = available
        summary["pending_payout"] = pending
        return summary

    def admin_summary(self):
        summary = self._base_summary()
        summary["orders_count"] = MarketplaceOrder.query.count()
        summary["paid_orders_count"] = MarketplaceOrder.query.filter_by(payment_status="paid").count()
        summary["refunded_orders_count"] = MarketplaceOrder.query.filter_by(payment_status="refunded").count()
        summary["gross_sales_amount"] = str(
            MarketplaceOrder.query.with_entities(func.coalesce(func.sum(MarketplaceOrder.gross_amount), 0)).scalar()
            or 0
        )
        summary["net_seller_amount"] = str(
            MarketplaceOrder.query.with_entities(func.coalesce(func.sum(MarketplaceOrder.net_seller_amount), 0)).scalar()
            or 0
        )
        summary["refunds_count"] = RefundRecord.query.count()
        summary["refunds_amount"] = str(
            RefundRecord.query.with_entities(func.coalesce(func.sum(RefundRecord.amount), 0)).scalar() or 0
        )
        summary["products_count"] = Product.query.count()
        summary["payouts_count"] = SellerPayout.query.count()
        summary["payouts_paid_amount"] = str(
            SellerPayout.query.filter_by(status="paid")
            .with_entities(func.coalesce(func.sum(SellerPayout.amount), 0))
            .scalar()
            or 0
        )
        summary["available_for_payout"] = str(
            SellerBalance.query.with_entities(func.coalesce(func.sum(SellerBalance.available_for_payout), 0)).scalar()
            or 0
        )
        summary["pending_payout"] = str(
            SellerBalance.query.with_entities(func.coalesce(func.sum(SellerBalance.pending_payout), 0)).scalar() or 0
        )
        return summary
