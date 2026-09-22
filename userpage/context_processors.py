from .models import Cart


def cart_count(request):
    """Global cart badge count for the storefront navbar."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"cart_count": 0}
    try:
        return {"cart_count": Cart.objects.filter(user=request.user).count()}
    except Exception:
        return {"cart_count": 0}
