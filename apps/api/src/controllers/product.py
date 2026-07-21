import json
import logging

from flask import Response, request
from flask.views import View

from serializers.productSerializers import ProductSerializer
from utils.user import schema_validation


def serialize_product(product):
    return {
        "uuid": product.uuid,
        "title": product.title,
        "description": product.description,
        "price": str(product.price),
        "currency": product.currency,
        "category": product.category,
        "is_active": product.is_active,
        "is_public": product.is_public,
        "owner_uuid": product.owner.uuid if product.owner else None,
        "owner_username": product.owner.username if product.owner else None,
        "created_on": product.created_on.isoformat() if product.created_on else None,
        "modified_on": product.modified_on.isoformat() if product.modified_on else None,
    }


class ProductCollection(View):
    methods = ["GET", "POST"]

    @schema_validation("ProductCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            serializer = ProductSerializer(payload)
            try:
                product = serializer.create()
            except Exception as e:
                logging.error(f"Product create error :: {e} :: {payload}")
                return Response(
                    response=json.dumps({"error": f"Error creating product {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )

            return Response(
                response=json.dumps(serialize_product(product)),
                status=201,
                mimetype="application/json",
            )

        serializer = ProductSerializer()
        products = serializer.list_public()
        return Response(
            response=json.dumps([serialize_product(product) for product in products]),
            status=200,
            mimetype="application/json",
        )


class ProductDetail(View):
    methods = ["GET"]

    def dispatch_request(self, product_uuid, *args, **kwargs):
        serializer = ProductSerializer()
        try:
            product = serializer.get_by_uuid(product_uuid)
        except Exception as e:
            return Response(
                response=json.dumps({"error": str(e)}),
                status=404,
                mimetype="application/json",
            )

        if not product.is_active or not product.is_public:
            return Response(
                response=json.dumps({"error": "Product not found"}),
                status=404,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serialize_product(product)),
            status=200,
            mimetype="application/json",
        )
