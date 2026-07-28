from models.ledger import MarketplaceOrder


class LedgerSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}

    def _serialize_order(self, order):
        return {
            "uuid": order.uuid,
            "buyer_uuid": order.buyer.uuid if order.buyer else None,
            "buyer_username": order.buyer.username if order.buyer else None,
            "seller_uuid": order.seller.uuid if order.seller else None,
            "seller_username": order.seller.username if order.seller else None,
            "product_uuid": order.product.uuid if order.product else None,
            "product_title": order.product.title if order.product else None,
            "gross_amount": str(order.gross_amount),
            "platform_fee": str(order.platform_fee),
            "tax_amount": str(order.tax_amount),
            "net_seller_amount": str(order.net_seller_amount),
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "refund_status": order.refund_status,
            "provider": order.provider,
            "provider_order_id": order.provider_order_id,
            "provider_payment_id": order.provider_payment_id,
            "created_on": order.created_on.isoformat() if order.created_on else None,
            "modified_on": order.modified_on.isoformat() if order.modified_on else None,
        }

    def list_orders(self):
        return MarketplaceOrder.query.order_by(MarketplaceOrder.created_on.desc()).all()

    def get_by_uuid(self, order_uuid):
        order = MarketplaceOrder.query.filter_by(uuid=order_uuid).first()
        if not order:
            raise ValueError("Marketplace order not found")
        return order

    def serialize_order(self, order):
        return self._serialize_order(order)
