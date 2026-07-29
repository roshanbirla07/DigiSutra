import base64
import hashlib
import hmac
import json
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from configuration.variables import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET


class RazorpayGatewayError(Exception):
    pass


class RazorpayGateway(object):
    BASE_URL = "https://api.razorpay.com/v1"

    def _auth_header(self):
        token = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode("utf-8")
        return base64.b64encode(token).decode("ascii")

    def _request(self, method, path, payload=None):
        url = f"{self.BASE_URL}{path}"
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
