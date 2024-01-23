from rest_framework import serializers
from ml.VEndpoints.models import VEndpoint
from ml.VEndpoints.models import VMLAlgorithm
from ml.VEndpoints.models import VMLAlgorithmStatus
from ml.VEndpoints.models import VMLRequest

class VEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = VEndpoint
        read_only_fields = ("id", "name", "owner", "created_at")
        fields = read_only_fields


class VMLAlgorithmSerializer(serializers.ModelSerializer):

    current_status = serializers.SerializerMethodField(read_only=True)

    def get_current_status(self, mlalgorithm):
        return VMLAlgorithmStatus.objects.filter(parent_mlalgorithm=mlalgorithm).latest('created_at').status

    class Meta:
        model = VMLAlgorithm
        read_only_fields = ("id", "name", "description", "code",
                            "version", "owner", "created_at",
                            "parent_endpoint", "current_status")
        fields = read_only_fields

class VMLAlgorithmStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VMLAlgorithmStatus
        read_only_fields = ("id", "active")
        fields = ("id", "active", "status", "created_by", "created_at",
                            "parent_mlalgorithm")

class VMLRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VMLRequest
        read_only_fields = (
            "id",
            "input_data",
            "full_response",
            "response",
            "created_at",
            "parent_mlalgorithm",
            "related_Video",
        )
        fields =  (
            "id",
            "input_data",
            "full_response",
            "response",
            "feedback",
            "created_at",
            "parent_mlalgorithm",
            "related_Video",
        )

