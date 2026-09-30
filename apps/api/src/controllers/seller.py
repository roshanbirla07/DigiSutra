import json
import logging

from flask import Response, request
from flask.views import View

from serializers.sellerSerializers import SellerApplicationSerializer
from utils.auth import require_auth
from utils.user import schema_validation


def _response(payload, status=200):
    return Response(response=json.dumps(payload), status=status, mimetype="application/json")


class SellerApplicationCollection(View):
    methods = ["GET", "POST", "PATCH"]

    @require_auth(roles=["customer"], methods=["GET", "POST", "PATCH"])
    @schema_validation("SellerApplication", methods=["POST", "PATCH"])
    def dispatch_request(self, *args, **kwargs):
        serializer = SellerApplicationSerializer
        try:
            if request.method == "GET":
                application = serializer.get_my_application()
                return _response(serializer.serialize_application(application) if application else {"application": None})
            application = serializer.save_draft(request.get_json(silent=True) or {})
            return _response(serializer.serialize_application(application), 200)
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application save/read error', type(exc).__name__)
            return _response({"error": str(exc)}, 400)


class SellerApplicationSubmit(View):
    methods = ["POST"]

    @require_auth(roles=["customer"], methods=["POST"])
    @schema_validation("SellerApplication", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        try:
            application = SellerApplicationSerializer.submit(request.get_json(silent=True) or {})
            return _response(SellerApplicationSerializer.serialize_application(application), 200)
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application submit error', type(exc).__name__)
            return _response({"error": str(exc)}, 400)


class SellerApplicationWithdraw(View):
    methods = ["POST"]

    @require_auth(roles=["customer"], methods=["POST"])
    def dispatch_request(self, application_uuid, *args, **kwargs):
        try:
            application = SellerApplicationSerializer.withdraw(application_uuid)
            return _response(SellerApplicationSerializer.serialize_application(application), 200)
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application withdraw error', type(exc).__name__)
            return _response({"error": str(exc)}, 400)


class AdminSellerApplicationCollection(View):
    methods = ["GET"]

    @require_auth(roles=["admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        try:
            applications = SellerApplicationSerializer.list_applications(request.args.get("status"))
            response = _response([SellerApplicationSerializer.serialize_application_summary(item) for item in applications])
            response.headers["Cache-Control"] = "no-store"
            return response
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application list error', type(exc).__name__)
            return _response({"error": str(exc)}, 400)


class AdminSellerApplicationDetail(View):
    methods = ["GET"]

    @require_auth(roles=["admin"], methods=["GET"])
    def dispatch_request(self, application_uuid, *args, **kwargs):
        try:
            application = SellerApplicationSerializer._get_owned(application_uuid)
            response = _response(SellerApplicationSerializer.serialize_application(application))
            response.headers["Cache-Control"] = "no-store"
            logging.info("event=admin_seller_application_detail application_uuid=%s", application_uuid)
            return response
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application detail error', type(exc).__name__)
            return _response({"error": str(exc)}, 404)


class AdminSellerApplicationReview(View):
    methods = ["POST"]

    action = None

    @require_auth(roles=["admin"], methods=["POST"])
    @schema_validation("SellerApplicationReview", methods=["POST"])
    def dispatch_request(self, application_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        try:
            if self.action == "request-information":
                result = SellerApplicationSerializer.request_information(application_uuid, payload.get("note"))
                return _response(SellerApplicationSerializer.serialize_application(result))
            if self.action == "reject":
                result = SellerApplicationSerializer.reject(application_uuid, payload.get("note"))
                return _response(SellerApplicationSerializer.serialize_application(result))
            if self.action == "start-kyc-review":
                result = SellerApplicationSerializer.start_kyc_review(application_uuid, payload)
                return _response(SellerApplicationSerializer.serialize_application(result))
            if self.action == "verify-kyc":
                result = SellerApplicationSerializer.verify_kyc(application_uuid, payload)
                return _response(SellerApplicationSerializer.serialize_application(result))
            if self.action == "fail-kyc":
                result = SellerApplicationSerializer.fail_kyc(application_uuid, payload)
                return _response(SellerApplicationSerializer.serialize_application(result))
            result, profile = SellerApplicationSerializer.approve(application_uuid, payload.get("note"))
            return _response({
                "application": SellerApplicationSerializer.serialize_application(result),
                "seller_profile": SellerApplicationSerializer.serialize_profile(profile),
            })
        except Exception as exc:
            logging.error("event=%s error_type=%s", 'Seller application review error', type(exc).__name__)
            return _response({"error": str(exc)}, 400)


class AdminSellerApplicationRequestInformation(AdminSellerApplicationReview):
    action = "request-information"


class AdminSellerApplicationReject(AdminSellerApplicationReview):
    action = "reject"


class AdminSellerApplicationApprove(AdminSellerApplicationReview):
    action = "approve"


class AdminSellerApplicationStartKycReview(AdminSellerApplicationReview):
    action = "start-kyc-review"


class AdminSellerApplicationVerifyKyc(AdminSellerApplicationReview):
    action = "verify-kyc"


class AdminSellerApplicationFailKyc(AdminSellerApplicationReview):
    action = "fail-kyc"
