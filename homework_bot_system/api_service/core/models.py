from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """النموذج الأساسي المشترك"""
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """مدير للحذف الناعم"""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(BaseModel):
    """نموذج الحذف الناعم"""
    
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='محذوف'
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحذف'
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """حذف ناعم"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self, using=None, keep_parents=False):
        """حذف نهائي"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """استعادة العنصر المحذوف"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])