from django.contrib.auth.decorators import login_required, user_passes_test


operator_group = user_passes_test(lambda u: True if u.is_operator else False)
def operator_required(view_func):
    decorated_view_func = login_required(operator_group(view_func))
    return decorated_view_func


customer_group = user_passes_test(lambda u: True if u.is_customer else False)
def customer_required(view_func):
    decorated_view_func = login_required(customer_group(view_func))
    return decorated_view_func
