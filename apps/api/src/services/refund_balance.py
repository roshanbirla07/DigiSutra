"""Reverse the seller share of a customer refund."""
from decimal import Decimal, ROUND_HALF_UP


def seller_refund_debit(order, refund_amount):
    gross = Decimal(str(order.gross_amount))
    seller_net = Decimal(str(order.net_seller_amount))
    amount = Decimal(str(refund_amount))
    if amount == gross:
        return seller_net
    return (seller_net * amount / gross).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
