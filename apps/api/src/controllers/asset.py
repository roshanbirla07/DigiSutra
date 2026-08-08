import json
import logging

from flask import g, Response, request
from flask.views import View
from werkzeug.exceptions import HTTPException

from serializers.assetSerializers import AssetSerializer
from utils.auth import require_auth, verify_delivery_token
from utils.user import schema_validation


class AssetUploadTarget(View):
    methods = ["POST"]

    @require_auth(roles=["seller", "admin"], methods=["POST"])
    @schema_validation("ProductAssetCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = AssetSerializer(payload)
        try:
            asset, presigned = serializer.create_upload_target(payload)
        except Exception as e:
            logging.error(f"Asset upload target error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error creating upload target {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        response_data = serializer.serialize_asset(asset)
        response_data["presigned_upload"] = presigned
        return Response(
            response=json.dumps(response_data),
            status=201,
            mimetype="application/json",
        )


class AssetDownloadLog(View):
    methods = ["POST"]

    @require_auth(methods=["POST"])
    def dispatch_request(self, asset_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        delivery_token = request.headers.get("X-Asset-Delivery-Token")
        serializer = AssetSerializer(payload)
        try:
            delivery_claims = verify_delivery_token(delivery_token)
            if delivery_claims.get("sub") != g.user.uuid:
                raise ValueError("Delivery token user mismatch")
            if delivery_claims.get("asset_uuid") != asset_uuid:
                raise ValueError("Delivery token asset mismatch")
            payload = dict(payload)
            payload["_delivery_claims"] = delivery_claims
            download = serializer.log_download(asset_uuid, payload)
        except Exception as e:
            logging.error(f"Asset download log error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error logging download {str(e)}"}),
                status=e.code if isinstance(e, HTTPException) else 400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_download(download)),
            status=201,
            mimetype="application/json",
        )


class AssetDownloadAuthorize(View):
    methods = ["POST"]

    @require_auth(methods=["POST"])
    def dispatch_request(self, asset_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = AssetSerializer(payload)
        try:
            delivery = serializer.authorize_download(asset_uuid, payload)
        except Exception as e:
            logging.error(f"Asset download authorize error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error authorizing download {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(delivery),
            status=200,
            mimetype="application/json",
        )


class AssetUploadComplete(View):
    methods = ["POST"]

    @require_auth(roles=["seller", "admin"], methods=["POST"])
    @schema_validation("ProductAssetComplete", methods=["POST"])
    def dispatch_request(self, asset_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = AssetSerializer(payload)
        try:
            asset = serializer.complete_upload(asset_uuid, payload)
        except Exception as e:
            logging.error(f"Asset upload completion error :: {e} :: {asset_uuid}")
            return Response(response=json.dumps({"error": f"Error completing upload {str(e)}"}), status=400, mimetype="application/json")
        return Response(response=json.dumps(serializer.serialize_asset(asset)), status=200, mimetype="application/json")
