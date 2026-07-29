import json
import logging

from flask import Response, request
from flask.views import View

from serializers.paymentSerializers import PaymentSerializer
from utils.user import schema_validation


class PaymentOrderCollection(View):
    methods = ["POST"]

    @schema_validation("PaymentOrderCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = PaymentSerializer(payload)
        try:
            order, provider_order = serializer.create_provider_order(payload["order_uuid"])
        except Exception as e:
            logging.error(f"Payment order create error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error creating payment order {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        response_data = serializer.serialize_order(order)
        if provider_order:
            response_data["razorpay_order"] = provider_order
        return Response(
            response=json.dumps(response_data),
            status=201,
            mimetype="application/json",
        )


class PaymentConfirm(View):
    methods = ["POST"]

    @schema_validation("PaymentConfirm", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = PaymentSerializer(payload)
        try:
            order = serializer.confirm_checkout_payment(payload)
        except Exception as e:
            logging.error(f"Payment confirm error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error confirming payment {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_order(order)),
            status=200,
            mimetype="application/json",
        )


class PaymentWebhook(View):
    methods = ["POST"]

    @schema_validation("PaymentWebhook", methods=["POST"], allow_unknown=True)
    def dispatch_request(self, *args, **kwargs):
        raw_body = request.get_data() or b""
        payload = request.get_json(silent=True) or {}
        payload["x_razorpay_signature"] = request.headers.get("X-Razorpay-Signature")
        serializer = PaymentSerializer(payload)
        try:
            order = serializer.process_webhook_event(payload, raw_body)
        except Exception as e:
            logging.error(f"Payment webhook error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Webhook rejected {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        if not order:
            return Response(
                response=json.dumps({"ignored": True}),
                status=200,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_order(order)),
            status=200,
            mimetype="application/json",
        )
