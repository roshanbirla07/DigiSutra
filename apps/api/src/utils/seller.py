from models.seller import SellerProfile


def seller_is_suspended(user):
    profile = SellerProfile.query.filter_by(user_id=user.id).first()
    return bool(profile and profile.is_suspended)


def require_operational_seller(user):
    if seller_is_suspended(user):
        raise ValueError("Seller account is suspended")
    return user
