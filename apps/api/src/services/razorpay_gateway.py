import base64
import hashlib
import hmac
import json
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from configuration.variables import PAYMENT_MODE, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET


class RazorpayGatewayError(Exception):
    pass


class RazorpayGateway(object):
    TEST_BASE_URL = "https://api.razorpay.com/v1"
    LIVE_BASE_URL = "https://api.razorpay.com/v1"

    def _base_url(self):
        mode = str(PAYMENT_MODE or "test").lower()
        if mode not in {"test", "live"}:
            raise RazorpayGatewayError("PAYMENT_MODE must be test or live")
        return self.LIVE_BASE_URL if mode == "live" else self.TEST_BASE_URL

    def _auth_header(self):
        token = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode("utf-8")
        return base64.b64encode(token).decode("ascii")

    def _request(self, method, path, payload=None):
        url = f"{self._base_url()}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(url, data=body, method=method.upper())
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Basic {self._auth_header()}")
        try:
            with urlrequest.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RazorpayGatewayError(exc.read().decode("utf-8"))
        except URLError as exc:
            raise RazorpayGatewayError(str(exc))

    def create_order(self, amount, currency="INR", receipt=None, notes=None):
        payload = {
            "amount": int(amount),
            "currency": currency,
        }
        if receipt:
            payload["receipt"] = receipt
        if notes:
            payload["notes"] = notes
        return self._request("POST", "/orders", payload)

    def create_refund(self, payment_id, amount, currency="INR", notes=None):
        if not payment_id:
            raise RazorpayGatewayError("Razorpay payment id is required for refund")
        payload = {"amount": int(amount), "currency": currency}
        if notes:
            payload["notes"] = notes
        return self._request("POST", f"/payments/{payment_id}/refund", payload)

    def mode(self):
        return str(PAYMENT_MODE or "test").lower()

    def verify_checkout_signature(self, order_id, payment_id, signature):
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, raw_body, signature):
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
