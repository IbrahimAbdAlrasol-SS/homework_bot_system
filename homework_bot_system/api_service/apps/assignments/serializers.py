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
            'created_by', 'created_by_name', 'due_date', 'priority',
            'status', 'max_points', 'allow_late_submission',
            'late_penalty_per_day', 'is_active', 'files',
            'submissions_count', 'pending_submissions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'submissions_count', 'pending_submissions']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class AssignmentDetailSerializer(AssignmentSerializer):
    recent_submissions = serializers.SerializerMethodField()
    
    class Meta(AssignmentSerializer.Meta):
        fields = AssignmentSerializer.Meta.fields + ['recent_submissions']
    
    def get_recent_submissions(self, obj):
        from apps.submissions.serializers import SubmissionSerializer
        recent = obj.submissions.select_related('user').order_by('-created_at')[:5]
        return SubmissionSerializer(recent, many=True).data

class CreateAssignmentSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'section', 'due_date',
            'priority', 'max_points', 'allow_late_submission',
            'late_penalty_per_day', 'files'
        ]
    
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