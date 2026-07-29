from utils.constants import USER_TYPE

UserCreateSchema = {
    'firstname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'lastname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
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
    'owner_uuid': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'title': {'type': 'string', 'maxlength': 150, 'nullable': False, 'required': True},
    'description': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'price': {'type': ['string', 'integer', 'float'], 'nullable': False, 'required': True},
    'currency': {'type': 'string', 'maxlength': 10, 'nullable': True, 'required': False},
    'category': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'is_active': {'type': 'boolean', 'nullable': True, 'required': False},
    'is_public': {'type': 'boolean', 'nullable': True, 'required': False},
}

LedgerOrderCreateSchema = {
    'uuid': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'buyer_uuid': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'seller_uuid': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'product_uuid': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
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
    'uuid': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'amount': {'type': ['string', 'integer', 'float'], 'nullable': True, 'required': False},
    'reason': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'status': {'type': 'string', 'maxlength': 30, 'nullable': True, 'required': False},
}

validationschema = {
    'UserCreate': UserCreateSchema,
    'UserLogin': UserLoginSchema,
    'ProductCreate': ProductCreateSchema,
    'LedgerOrderCreate': LedgerOrderCreateSchema,
    'LedgerRefundCreate': LedgerRefundCreateSchema,
}
