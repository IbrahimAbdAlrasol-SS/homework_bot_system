from rest_framework import serializers
from django.utils import timezone
from .models import Submission, SubmissionFile
from apps.assignments.serializers import AssignmentSerializer
from apps.users.serializers import UserProfileSerializer


class SubmissionFileSerializer(serializers.ModelSerializer):
    """مسلسل ملفات التسليم"""
    
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = SubmissionFile
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_size_mb',
            'file_type', 'uploaded_at'
        ]
        read_only_fields = ['id', 'file_size', 'file_type', 'uploaded_at']
    
    def get_file_size_mb(self, obj):
        """حجم الملف بالميجابايت"""
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size else 0


class SubmissionSerializer(serializers.ModelSerializer):
    """مسلسل التسليمات"""
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    files = SubmissionFileSerializer(many=True, read_only=True)
    is_overdue = serializers.SerializerMethodField()
    time_until_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'student', 'student_name', 'assignment_title',
            'content', 'status', 'grade', 'points_earned', 'is_late',
            'is_excellent', 'reviewed_by', 'reviewed_at', 'feedback',
            'files', 'is_overdue', 'time_until_deadline', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student', 'points_earned', 'is_late', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]
    
    def get_is_overdue(self, obj):
        """هل انتهى الموعد النهائي"""
        return timezone.now() > obj.assignment.deadline
    
    def get_time_until_deadline(self, obj):
        """الوقت المتبقي حتى الموعد النهائي"""
        time_diff = obj.assignment.deadline - timezone.now()
        if time_diff.total_seconds() > 0:
            days = time_diff.days
            hours = time_diff.seconds // 3600
            return f"{days} يوم و {hours} ساعة"
        return "انتهى الموعد"


class SubmissionDetailSerializer(SubmissionSerializer):
    """مسلسل تفاصيل التسليم"""
    
    assignment = AssignmentSerializer(read_only=True)
    student = UserProfileSerializer(read_only=True)
    reviewed_by = UserProfileSerializer(read_only=True)
    
    class Meta(SubmissionSerializer.Meta):
        fields = SubmissionSerializer.Meta.fields + ['assignment', 'student']


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء التسليم"""
    
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Submission
        fields = ['assignment', 'content', 'files']
    
    def create(self, validated_data):
        files_data = validated_data.pop('files', [])
        validated_data['student'] = self.context['request'].user
        
        submission = Submission.objects.create(**validated_data)
        
        # إضافة الملفات
        for file_data in files_data:
            SubmissionFile.objects.create(
                submission=submission,
                file=file_data,
                file_name=file_data.name
            )
        
        return submission


class SubmissionReviewSerializer(serializers.ModelSerializer):
    """مسلسل مراجعة التسليم"""
    
    class Meta:
        model = Submission
        fields = ['status', 'grade', 'feedback', 'is_excellent']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        
        if status == Submission.Status.APPROVED:
            instance.approve(
                reviewed_by=self.context['request'].user,
                feedback=validated_data.get('feedback', ''),
                is_excellent=validated_data.get('is_excellent', False)
            )
        elif status == Submission.Status.REJECTED:
            instance.reject(
                reviewed_by=self.context['request'].user,
                feedback=validated_data.get('feedback', '')
            )
        else:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
        
        return instance


class SubmissionStatisticsSerializer(serializers.Serializer):
    """مسلسل إحصائيات التسليمات"""
    
    total_submissions = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    late_submissions = serializers.IntegerField()
    excellent_submissions = serializers.IntegerField()
    approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_points = serializers.DecimalField(max_digits=10, decimal_places=2)