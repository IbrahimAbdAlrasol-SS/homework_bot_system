from rest_framework import serializers
from .models import Assignment, AssignmentFile
from apps.sections.models import Section
from apps.users.models import User

class AssignmentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentFile
        fields = ['id', 'file', 'file_name', 'file_size', 'uploaded_at']
        read_only_fields = ['file_size', 'uploaded_at']

class AssignmentSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    files = AssignmentFileSerializer(many=True, read_only=True)
    submissions_count = serializers.IntegerField(read_only=True)
    pending_submissions = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'section', 'section_name',
            'created_by', 'created_by_name', 'due_date', 'priority',  # ✅ إصلاح الاسم
            'status', 'points_value', 'allow_late_submission',  # ✅ توحيد النقاط
            'late_penalty_per_day', 'is_active', 'files',
            'submissions_count', 'pending_submissions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'submissions_count', 'pending_submissions']

class CreateAssignmentSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'section', 'due_date',  # ✅ إصلاح الاسم
            'priority', 'points_value', 'allow_late_submission',  # ✅ توحيد النقاط
            'late_penalty_per_day', 'files'
        ]
    
    def validate_due_date(self, value):
        """التحقق من صحة الموعد النهائي"""
        if value <= timezone.now():
            raise serializers.ValidationError("الموعد النهائي يجب أن يكون في المستقبل")
        return value
    
    def create(self, validated_data):
        files_data = validated_data.pop('files', [])
        validated_data['created_by'] = self.context['request'].user
        
        assignment = Assignment.objects.create(**validated_data)
        
        # إضافة الملفات
        for file_data in files_data:
            AssignmentFile.objects.create(
                assignment=assignment,
                file=file_data,
                file_name=file_data.name
            )
        
        return assignment