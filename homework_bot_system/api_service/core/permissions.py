from rest_framework import permissions
from apps.users.models import User

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    صلاحية مخصصة للسماح للأدمن بالتعديل والقراءة للجميع
    """
    
    def has_permission(self, request, view):
        # السماح بالقراءة للجميع
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # السماح بالكتابة للأدمن فقط
        return request.user.is_authenticated and request.user.is_admin

class IsSuperAdminOnly(permissions.BasePermission):
    """
    صلاحية للمسؤول العام فقط
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == User.Role.SUPER_ADMIN
        )

class IsSectionAdminOrOwner(permissions.BasePermission):
    """
    صلاحية لأدمن الشعبة أو صاحب البيانات
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # المسؤول العام يمكنه الوصول لكل شيء
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # أدمن الشعبة يمكنه الوصول لبيانات شعبته
        if request.user.role == User.Role.SECTION_ADMIN:
            if hasattr(obj, 'section'):
                return obj.section == request.user.section
            elif hasattr(obj, 'user'):
                return obj.user.section == request.user.section
        
        # الطالب يمكنه الوصول لبياناته فقط
        if request.user.role == User.Role.STUDENT:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return obj == request.user
        
        return False

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    صلاحية لصاحب البيانات أو الأدمن
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # الأدمن يمكنه الوصول لكل شيء
        if request.user.is_admin:
            return True
        
        # صاحب البيانات
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user

class IsStudentOnly(permissions.BasePermission):
    """
    صلاحية للطلاب فقط
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == User.Role.STUDENT
        )