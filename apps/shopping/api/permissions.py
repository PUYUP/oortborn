from apps.shopping.admin import Basket
from rest_framework import permissions, viewsets


class ViewsPermission(viewsets.ViewSet):
    """
    Instantiates and returns
    the list of permissions that this view requires.
    """

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


class IsCanUpdateBasket(permissions.BasePermission):
    """
    Boleh update Basket jika;
    - current user adalah creator Basket
    - current user boleh membeli (is_can_buy)
    """

    def has_object_permission(self, request, view, obj):
        share_obj = obj.share.filter(to_user_id=request.user.id)
        is_can_buy = share_obj.filter(is_can_buy=True).exists()

        if request.user.uuid == obj.user.uuid or is_can_buy:
            return True


class IsBasketCreatorOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid


class IsBasketShareAsAdminOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid


class IsBasketOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.basket_owner.uuid


class IsCanCreateStuff(permissions.BasePermission):
    """
    Boleh tambah Stuff jika:
    - current user sama dengan pembuat Basket
    - current user berperan Admin (is_admin)
    - current user boleh menambahkan (is_can_crud)
    """

    def has_permission(self, request, view):
        basket_uuid = request.data.get('basket')
        if basket_uuid:
            try:
                basket_obj = Basket.objects.get(uuid=basket_uuid)
            except Exception as e:
                return False

            share_obj = basket_obj.share.filter(to_user_id=request.user.id)
            is_admin = share_obj.filter(is_admin=True).exists()
            is_can_crud = share_obj.filter(is_can_crud=True).exists()

            if basket_obj.user.uuid == request.user.uuid or is_admin:
                return True

            if is_can_crud:
                return True

            return False
        return False


class IsCanUpdateStuff(permissions.BasePermission):
    """
    - current user sama dengan pembuat Basket
    - atau current user berperan Admin (is_admin)
    - atau current user boleh menambahkan (is_can_crud)
    - dan jika Stuff belum Purchased
    """

    def has_object_permission(self, request, view, obj):
        share_obj = obj.basket.share.filter(to_user_id=request.user.id)
        is_admin = share_obj.filter(is_admin=True).exists()
        is_can_crud = share_obj.filter(is_can_crud=True).exists()

        if hasattr(obj, 'purchased_stuff'):
            if request.user.uuid != obj.purchased_stuff.user.uuid:
                return False

        if request.user.uuid == obj.basket.user.uuid or is_admin:
            return True

        if request.user.uuid == obj.user.uuid and is_can_crud:
            return True

        return False


class IsCanDeleteStuff(permissions.BasePermission):
    """
    - current user sama dengan pembuat Basket
    - atau current user boleh menambahkan (is_can_crud)
    - dan belanja belum selesai
    - dan hanya jika Stuff belum di Purchased
    """

    def has_object_permission(self, request, view, obj):
        share_obj = obj.basket.share.filter(to_user_id=request.user.id)
        
        if not obj.basket.is_complete:
            is_admin = share_obj.filter(is_admin=True).exists()
            is_can_crud = share_obj.filter(is_can_crud=True).exists()

            if hasattr(obj, 'purchased_stuff'):
                if request.user.uuid != obj.purchased_stuff.user.uuid:
                    return False

            if request.user.uuid == obj.basket.user.uuid or is_admin:
                return True

            if request.user.uuid == obj.user.uuid and is_can_crud:
                return True

            return False
        return False


class IsCanCreatePurchased(permissions.BasePermission):
    """
    - current user sama dengan pembuat Basket
    - atau current user boleh membeli (is_can_buy)
    """

    def has_permission(self, request, view):
        basket_uuid = request.data.get('basket')
        if basket_uuid:
            try:
                basket_obj = Basket.objects.get(uuid=basket_uuid)
            except Exception as e:
                return False
            
            # current user is creator of basket
            if basket_obj.user.uuid == request.user.uuid:
                return True

            share_obj = basket_obj.share.filter(to_user_id=request.user.id)
            is_can_buy = share_obj.filter(is_can_buy=True).exists()

            if is_can_buy:
                return True

            return False
        return False


IsCanCreatePurchasedStuff = IsCanCreatePurchased


class IsCanUpdatePurchasedStuff(permissions.BasePermission):
    """
    - current user sama dengan pembuatnya
    - dan current user boleh membeli (is_can_buy)
    """

    def has_object_permission(self, request, view, obj):
        basket_obj = obj.basket
        share_obj = basket_obj.share.filter(to_user_id=request.user.id)
        is_can_buy = share_obj.filter(is_can_buy=True).exists()

        if request.user.uuid == obj.user.uuid and is_can_buy:
            return False
        return False


class IsCanDeletePurchasedStuff(permissions.BasePermission):
    """current user sama dengan pembuatnya"""
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid


class IsObjectOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid


class IsCanUpdateShare(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if (request.user.uuid == obj.user.uuid) or (request.user.uuid == obj.to_user.uuid):
            return True
        return False
