from rest_framework import serializers

from .models import Appointment, Doctor, Patient


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ["id", "name", "specialty"]


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "name", "phone", "email"]
        extra_kwargs = {"email": {"required": False, "allow_blank": True}}

    def validate_phone(self, value):
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 9:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "doctor", "patient", "start_time", "end_time",
            "status", "notes", "cancel_reason", "cancelled_at",
        ]


class BookAppointmentSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField(min_value=1)
    patient_id = serializers.IntegerField(min_value=1)
    start_time = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class RescheduleSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
