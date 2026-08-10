from utils.constants import USER_TYPE

UserCreateSchema = {
    'firstname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'first_name': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'lastname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'last_name': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'username': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'password': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'user_type': {'type': 'string', 'allowed': USER_TYPE.values() + ['creator'], 'nullable': True, 'required': False},
}

UserLoginSchema = {
    'username': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'password': {'type': 'string', 'maxlength': 128, 'nullable': False, 'required': True},
}

ProductCreateSchema = {
    'owner_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'title': {'type': 'string', 'maxlength': 150, 'nullable': False, 'required': True},
    'description': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'price': {'type': ['string', 'integer', 'float'], 'nullable': False, 'required': True},
    'currency': {'type': 'string', 'maxlength': 10, 'nullable': True, 'required': False},
    'category': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'image_uri': {'type': 'string', 'maxlength': 2048, 'nullable': True, 'required': False},
    'image_alt': {'type': 'string', 'maxlength': 255, 'nullable': True, 'required': False},
    'image_provider': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'image_key': {'type': 'string', 'maxlength': 255, 'nullable': True, 'required': False},
    'image_mime_type': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'image_size_bytes': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
    'image_width': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
    'image_height': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
    'image_sort_order': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
    'image_is_primary': {'type': 'boolean', 'nullable': True, 'required': False},
    'is_active': {'type': 'boolean', 'nullable': True, 'required': False},
    'is_public': {'type': 'boolean', 'nullable': True, 'required': False},
}

ProductAssetCreateSchema = {
    'product_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'original_filename': {'type': 'string', 'maxlength': 255, 'nullable': True, 'required': False},
    'content_type': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'size_bytes': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
}

ProductAssetCompleteSchema = {
    'size_bytes': {'type': ['string', 'integer'], 'nullable': True, 'required': False},
    'checksum_sha256': {'type': 'string', 'maxlength': 64, 'nullable': True, 'required': False},
}

LedgerOrderCreateSchema = {
    'uuid': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'buyer_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'seller_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'product_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'gross_amount': {'type': ['string', 'integer', 'float'], 'nullable': False, 'required': True},
    'platform_fee': {'type': ['string', 'integer', 'float'], 'nullable': True, 'required': False},
    'tax_amount': {'type': ['string', 'integer', 'float'], 'nullable': True, 'required': False},
    'payment_status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'delivery_status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'refund_status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'provider': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'provider_order_id': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'provider_payment_id': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
}

LedgerRefundCreateSchema = {
    'uuid': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'amount': {'type': ['string', 'integer', 'float'], 'nullable': True, 'required': False},
    'reason': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
}

PaymentOrderCreateSchema = {
    'order_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
}

PaymentConfirmSchema = {
    'razorpay_order_id': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'razorpay_payment_id': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'razorpay_signature': {'type': 'string', 'maxlength': 256, 'nullable': False, 'required': True},
}

PaymentWebhookSchema = {
    'entity': {'type': 'string', 'maxlength': 20, 'nullable': False, 'required': True},
    'event': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'payload': {'type': 'dict', 'nullable': False, 'required': True},
}

PayoutCreateSchema = {
    'uuid': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'seller_uuid': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'amount': {'type': ['string', 'integer', 'float'], 'nullable': False, 'required': True},
    'status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'payout_method': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'batch_id': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'failure_reason': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
}

PayoutBatchProcessSchema = {
    'batch_id': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'payout_updates': {'type': 'list', 'nullable': False, 'required': True},
}

SellerApplicationSchema = {
    'store_name': {'type': 'string', 'maxlength': 120, 'nullable': True, 'required': False},
    'store_description': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'category': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'product_types': {'type': 'string', 'maxlength': 1000, 'nullable': True, 'required': False},
    'website_url': {'type': 'string', 'maxlength': 2048, 'nullable': True, 'required': False},
    'portfolio_url': {'type': 'string', 'maxlength': 2048, 'nullable': True, 'required': False},
    'legal_name': {'type': 'string', 'maxlength': 120, 'nullable': True, 'required': False},
    'business_type': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'business_address': {'type': 'string', 'maxlength': 500, 'nullable': True, 'required': False},
    'pan_number': {'type': 'string', 'maxlength': 10, 'nullable': True, 'required': False},
    'gstin': {'type': 'string', 'maxlength': 15, 'nullable': True, 'required': False},
    'country': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'phone_number': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'bank_account_holder_name': {'type': 'string', 'maxlength': 120, 'nullable': True, 'required': False},
    'bank_account_last4': {'type': 'string', 'maxlength': 4, 'nullable': True, 'required': False},
    'bank_ifsc': {'type': 'string', 'maxlength': 11, 'nullable': True, 'required': False},
    'kyc_document_type': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'kyc_document_reference': {'type': 'string', 'maxlength': 500, 'nullable': True, 'required': False},
    'terms_accepted': {'type': 'boolean', 'nullable': True, 'required': False},
}

SellerApplicationReviewSchema = {
    'note': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'provider': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'provider_account_id': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'provider_account_status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
    'fund_account_status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
}

validationschema = {
    'UserCreate': UserCreateSchema,
    'UserLogin': UserLoginSchema,
    'ProductCreate': ProductCreateSchema,
    'ProductAssetCreate': ProductAssetCreateSchema,
    'ProductAssetComplete': ProductAssetCompleteSchema,
    'LedgerOrderCreate': LedgerOrderCreateSchema,
    'LedgerRefundCreate': LedgerRefundCreateSchema,
    'PaymentOrderCreate': PaymentOrderCreateSchema,
    'PaymentConfirm': PaymentConfirmSchema,
    'PaymentWebhook': PaymentWebhookSchema,
    'PayoutCreate': PayoutCreateSchema,
    'PayoutBatchProcess': PayoutBatchProcessSchema,
    'SellerApplication': SellerApplicationSchema,
    'SellerApplicationReview': SellerApplicationReviewSchema,
}
