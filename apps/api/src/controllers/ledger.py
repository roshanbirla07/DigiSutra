import json

from flask import Response
from flask.views import View

from serializers.ledgerSerializers import LedgerSerializer


class LedgerCollection(View):
    methods = ["GET"]

    def dispatch_request(self, *args, **kwargs):
        serializer = LedgerSerializer()
        orders = serializer.list_orders()
        return Response(
            response=json.dumps([serializer.serialize_order(order) for order in orders]),
            status=200,
            mimetype="application/json",
        )


class LedgerDetail(View):
    methods = ["GET"]

    def dispatch_request(self, order_uuid, *args, **kwargs):
        serializer = LedgerSerializer()
        try:
            order = serializer.get_by_uuid(order_uuid)
        except Exception as e:
            return Response(
                response=json.dumps({"error": str(e)}),
                status=404,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_order(order)),
            status=200,
            mimetype="application/json",
        )
