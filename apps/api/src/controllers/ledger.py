import json

import logging

from flask import Response, request, g
from flask.views import View

from serializers.ledgerSerializers import LedgerSerializer
from utils.auth import require_auth
from utils.user import schema_validation


class BuyerPurchaseHistory(View):
    methods = ["GET"]

    @require_auth(roles=["customer", "seller", "admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = LedgerSerializer()
        buyer = getattr(g, "user", None)
        history = serializer.list_buyer_purchases(buyer.id)
        return Response(
            response=json.dumps(history),
            status=200,
            mimetype="application/json",
        )


class LedgerCollection(View):
    methods = ["GET", "POST"]

    @require_auth(roles=["customer", "seller", "admin"], methods=["GET", "POST"])
    @schema_validation("LedgerOrderCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            serializer = LedgerSerializer(payload)
            try:
                order = serializer.create()
            except Exception as e:
                logging.error(f"Ledger order create error :: {e} :: {payload}")
                return Response(
                    response=json.dumps({"error": f"Error creating ledger order {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )

            return Response(
                response=json.dumps(serializer.serialize_order(order)),
                status=201,
                mimetype="application/json",
            )

        serializer = LedgerSerializer()
        user = getattr(g, "user", None)
        if str(user.user_type).lower() == "admin":
            orders = serializer.list_orders()
        elif str(user.user_type).lower() == "seller":
            orders = serializer.list_orders_for_seller(user.id)
        else:
            orders = serializer.list_orders_for_buyer(user.id)
        return Response(
            response=json.dumps([serializer.serialize_order(order) for order in orders]),
            status=200,
            mimetype="application/json",
        )


class LedgerDetail(View):
    methods = ["GET", "POST"]

    @require_auth(roles=["customer", "seller", "admin"], methods=["GET", "POST"])
    @schema_validation("LedgerRefundCreate", methods=["POST"])
    def dispatch_request(self, order_uuid, *args, **kwargs):
        serializer = LedgerSerializer()
        user = getattr(g, "user", None)
        try:
            order = serializer.get_by_uuid(order_uuid)
        except Exception as e:
            return Response(
                response=json.dumps({"error": str(e)}),
                status=404,
                mimetype="application/json",
            )

        is_admin = str(user.user_type).lower() == "admin"
        owns_order = user.id in {order.buyer_id, order.seller_id}
        if not is_admin and not owns_order:
            return Response(
                response=json.dumps({"error": "You do not have access to this order"}),
                status=403,
                mimetype="application/json",
            )

        if request.method == "POST":
            if not is_admin and user.id != order.buyer_id:
                return Response(
                    response=json.dumps({"error": "Only the buyer or an admin can request a refund"}),
                    status=403,
                    mimetype="application/json",
                )
            payload = request.get_json(silent=True) or {}
            try:
                refund = serializer.create_refund(order_uuid, payload)
            except Exception as e:
                logging.error(f"Ledger refund create error :: {e} :: {payload} :: {order_uuid}")
                return Response(
                    response=json.dumps({"error": f"Error creating refund {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )

            return Response(
                response=json.dumps(serializer.serialize_refund(refund)),
                status=201,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_order(order)),
            status=200,
            mimetype="application/json",
        )
