from models.ledger import MarketplaceOrder, RefundRecord, SellerPayout


class OpsSerializer(object):
    def serialize_order(self, order):
        return {
            "uuid": order.uuid,
            "buyer_uuid": order.buyer.uuid if order.buyer else None,
            "seller_uuid": order.seller.uuid if order.seller else None,
            "product_uuid": order.product.uuid if order.product else None,
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "refund_status": order.refund_status,
            "provider": order.provider,
            "provider_order_id": order.provider_order_id,
            "provider_payment_id": order.provider_payment_id,
            "created_on": order.created_on.isoformat() if order.created_on else None,
        }

    def serialize_refund(self, refund):
        return {
            "uuid": refund.uuid,
            "order_uuid": refund.order.uuid if refund.order else None,
            "status": refund.status,
            "amount": str(refund.amount),
            "reason": refund.reason,
            "provider_refund_id": refund.provider_refund_id,
            "provider_status": refund.provider_status,
            "failure_reason": refund.failure_reason,
            "created_on": refund.created_on.isoformat() if refund.created_on else None,
        }

    def serialize_payout(self, payout):
        return {
            "uuid": payout.uuid,
            "seller_uuid": payout.seller.uuid if payout.seller else None,
            "amount": str(payout.amount),
            "status": payout.status,
            "failure_reason": payout.failure_reason,
            "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
            "created_on": payout.created_on.isoformat() if payout.created_on else None,
        }

    def summary(self):
        failed_payments = MarketplaceOrder.query.filter_by(payment_status="failed").all()
        stuck_refunds = RefundRecord.query.filter(RefundRecord.status.in_(["requested", "approved"])).all()
        open_payouts = SellerPayout.query.filter(SellerPayout.status.in_(["pending", "processing", "failed"])).all()
        return {
            "failed_payments": [self.serialize_order(order) for order in failed_payments],
            "stuck_refunds": [self.serialize_refund(refund) for refund in stuck_refunds],
            "open_payouts": [self.serialize_payout(payout) for payout in open_payouts],
            "counts": {
                "failed_payments": len(failed_payments),
                "stuck_refunds": len(stuck_refunds),
                "open_payouts": len(open_payouts),
            },
        }
