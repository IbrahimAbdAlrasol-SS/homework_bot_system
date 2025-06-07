from rest_framework import serializers
from .models import Section
from apps.users.models import User

class SectionSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Section
        fields = [
            'id', 'name', 'study_type', 'admin', 'admin_name',
            'telegram_group_id', 'telegram_channel_id', 'is_active',
            'max_students', 'student_count', 'is_full', 'created_at'
        ]

class SectionDetailSerializer(SectionSerializer):
    students = serializers.SerializerMethodField()
    active_assignments_count = serializers.IntegerField(read_only=True)
    
    class Meta(SectionSerializer.Meta):
        fields = SectionSerializer.Meta.fields + [
            'students', 'active_assignments_count'
        ]
    
    def get_students(self, obj):
        from apps.users.serializers import UserSerializer
        students = obj.students.filter(is_active=True)[:10]  # Top 10
        return UserSerializer(students, many=True).data

class SectionStatisticsSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    completed_assignments = serializers.IntegerField()
    average_submission_rate = serializers.FloatField()
    top_students = serializers.ListField()