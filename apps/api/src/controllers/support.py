import json
import logging

from flask import Response, request
from flask.views import View

from serializers.supportSerializers import SupportSerializer
from utils.auth import require_auth


class SupportTicketCollection(View):
    methods = ["GET", "POST"]

    @require_auth(roles=["customer", "seller", "admin"], methods=["POST", "GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = SupportSerializer()
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            try:
                ticket = serializer.create_ticket(payload)
            except Exception as e:
                logging.error(f"Support ticket create error :: {e} :: {payload}")
                return Response(
                    response=json.dumps({"error": f"Error creating support ticket {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )
            return Response(
                response=json.dumps(serializer.serialize_ticket(ticket)),
                status=201,
                mimetype="application/json",
            )

        tickets = serializer.list_tickets()
        return Response(
            response=json.dumps([serializer.serialize_ticket(ticket) for ticket in tickets]),
            status=200,
            mimetype="application/json",
        )


class SupportTicketResolve(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, ticket_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = SupportSerializer()
        try:
            ticket = serializer.resolve_ticket(ticket_uuid, payload)
        except Exception as e:
            logging.error(f"Support ticket resolve error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error resolving support ticket {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps(serializer.serialize_ticket(ticket)),
            status=200,
            mimetype="application/json",
        )


class ProductFlagCollection(View):
    methods = ["POST"]

    @require_auth(roles=["customer", "seller", "admin"], methods=["POST"])
    def dispatch_request(self, product_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = SupportSerializer()
        try:
            flag = serializer.create_product_flag(product_uuid, payload)
        except Exception as e:
            logging.error(f"Product flag create error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error creating product flag {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps(serializer.serialize_flag(flag)),
            status=201,
            mimetype="application/json",
        )


class ProductFlagResolve(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, flag_uuid, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = SupportSerializer()
        try:
            flag = serializer.resolve_product_flag(flag_uuid, payload.get("status"))
        except Exception as e:
            logging.error(f"Product flag resolve error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error resolving product flag {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps(serializer.serialize_flag(flag)),
            status=200,
            mimetype="application/json",
        )


class UserSuspend(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, user_uuid, *args, **kwargs):
        serializer = SupportSerializer()
        try:
            user = serializer.set_user_active_state(user_uuid, False)
        except Exception as e:
            logging.error(f"User suspend error :: {e} :: {user_uuid}")
            return Response(
                response=json.dumps({"error": f"Error suspending user {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps({"uuid": user.uuid, "is_active": user.is_active}),
            status=200,
            mimetype="application/json",
        )


class UserActivate(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, user_uuid, *args, **kwargs):
        serializer = SupportSerializer()
        try:
            user = serializer.set_user_active_state(user_uuid, True)
        except Exception as e:
            logging.error(f"User activate error :: {e} :: {user_uuid}")
            return Response(
                response=json.dumps({"error": f"Error activating user {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps({"uuid": user.uuid, "is_active": user.is_active}),
            status=200,
            mimetype="application/json",
        )
