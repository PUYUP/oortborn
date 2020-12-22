from django.contrib.auth.decorators import login_required, user_passes_test


operator_group = user_passes_test(lambda u: True if u.is_operator else False)
def operator_required(view_func):
    decorated_view_func = login_required(operator_group(view_func))
    return decorated_view_func


buyer_group = user_passes_test(lambda u: True if u.is_buyer else False)
def buyer_required(view_func):
    decorated_view_func = login_required(buyer_group(view_func))
    return decorated_view_func
