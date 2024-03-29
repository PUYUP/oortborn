# THIRD PARTY
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'person': {
                'token': reverse('person_api:token_obtain_pair', request=request,
                                 format=format, current_app='person'),
                'token-refresh': reverse('person_api:token_refresh', request=request,
                                         format=format, current_app='person'),
                'users': reverse('person_api:user-list', request=request,
                                 format=format, current_app='person'),
                'verifycodes': reverse('person_api:verifycode-list', request=request,
                                       format=format, current_app='person'),
            },
            'shopping': {
                'customer': {
                    'baskets': reverse('shopping_api:customer:basket-list', request=request,
                                         format=format, current_app='shopping'),
                    'stuffs': reverse('shopping_api:customer:stuff-list', request=request,
                                         format=format, current_app='shopping'),
                    'purchaseds': reverse('shopping_api:customer:purchased-list', request=request,
                                         format=format, current_app='shopping'),
                    'purchased-stuffs': reverse('shopping_api:customer:purchased_stuff-list', request=request,
                                                  format=format, current_app='shopping'),
                    'circles': reverse('shopping_api:customer:circle-list', request=request,
                                       format=format, current_app='shopping'),
                    'shares': reverse('shopping_api:customer:share-list', request=request,
                                          format=format, current_app='shopping'),
                    'orders': reverse('shopping_api:customer:order-list', request=request,
                                      format=format, current_app='shopping'),
                    'order-lines': reverse('shopping_api:customer:order_line-list', request=request,
                                           format=format, current_app='shopping'),
                    'order-schedules': reverse('shopping_api:customer:order_schedule-list', request=request,
                                               format=format, current_app='shopping'),
                },
                'master': {
                    'products': reverse('shopping_api:master:product-list', request=request,
                                      format=format, current_app='shopping'),
                    'product-rates': reverse('shopping_api:master:product_rate-list', request=request,
                                           format=format, current_app='shopping'),
                }
            }
        })
