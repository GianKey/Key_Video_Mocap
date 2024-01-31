import json
import os
from numpy.random import rand
from urllib.parse import urlsplit

from django.db import transaction
from django.shortcuts import render
from rest_framework.exceptions import APIException

from helpers import AdminUserRequiredMixin

from django.views import generic
# Create your views here.
from rest_framework import viewsets,views,status
from rest_framework import mixins
from rest_framework.response import Response

from ml.VEndpoints.models import VEndpoint
from ml.VEndpoints.serializers import VEndpointSerializer

from ml.VEndpoints.models import VMLAlgorithm
from ml.VEndpoints.serializers import VMLAlgorithmSerializer

from ml.VEndpoints.models import VMLAlgorithmStatus
from ml.VEndpoints.serializers import VMLAlgorithmStatusSerializer

from ml.VEndpoints.models import VMLRequest
from ml.VEndpoints.serializers import VMLRequestSerializer

from helpers import get_page_list, ajax_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from ml.mlModel.registry import MLRegistry
from videoproject.wsgi import  mmpose_registry
from videoproject import  settings as globalsettings
class VMLAlgorithmListView(AdminUserRequiredMixin, generic.ListView):
    model = VMLAlgorithm
    template_name = 'ml/vmlalgorithm_list.html'
    context_object_name = 'vmlalgorithm_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VMLAlgorithmListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        return VMLAlgorithm.objects.filter(description__contains=self.q).order_by('-created_at')

@ajax_required
@require_http_methods(["POST"])
def vmlalgorithm_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    vmlalgorithm_id = request.POST['vmlalgorithm_id']
    instance = VMLAlgorithm.objects.get(id=vmlalgorithm_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class VEndpointViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = VEndpointSerializer
    queryset = VEndpoint.objects.all()

def deactivate_other_statuses(instance):
    old_statuses = VMLAlgorithmStatus.objects.filter(parent_mlalgorithm = instance.parent_mlalgorithm,
                                                        created_at__lt=instance.created_at,
                                                        active=True)
    for i in range(len(old_statuses)):
        old_statuses[i].active = False
    VMLAlgorithmStatus.objects.bulk_update(old_statuses, ["active"])

class VMLAlgorithmViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = VMLAlgorithmSerializer
    queryset = VMLAlgorithm.objects.all()

    def get(self, request, *args, **kwargs):
        # 处理GET请求的逻辑
        pass

    def post(self, request, *args, **kwargs):
        # 处理POST请求的逻辑
        pass
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)
        except Exception as e:
            raise APIException(str(e))



class VMLAlgorithmStatusViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.CreateModelMixin
):
    serializer_class = VMLAlgorithmStatusSerializer
    queryset = VMLAlgorithmStatus.objects.all()

    def get(self, request, *args, **kwargs):
        # 处理GET请求的逻辑
        pass

    def post(self, request, *args, **kwargs):
        # 处理POST请求的逻辑
        pass
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)



        except Exception as e:
            raise APIException(str(e))

class VMLRequestViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.UpdateModelMixin
):
    serializer_class = VMLRequestSerializer
    queryset = VMLRequest.objects.all()


# class VPredictView(views.APIView):
#     def post(self, request, endpoint_name, format=None):
#
#         algorithm_status = self.request.query_params.get("status", "production")
#         algorithm_version = self.request.query_params.get("version")
#
#         algs = VMLAlgorithm.objects.filter(parent_endpoint__name = endpoint_name, status__status = algorithm_status, status__active=True)
#
#         if algorithm_version is not None:
#             algs = algs.filter(version = algorithm_version)
#
#         if len(algs) == 0:
#             return Response(
#                 {"status": "Error", "message": "ML algorithm is not available"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         if len(algs) != 1 and algorithm_status != "ab_testing":
#             return Response(
#                 {"status": "Error", "message": "ML algorithm selection is ambiguous. Please specify algorithm version."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         alg_index = 0
#         if algorithm_status == "ab_testing":
#             alg_index = 0 if rand() < 0.5 else 1
#
#         algorithm_object = vregistry.endpoints[algs[alg_index].id]
#         prediction = algorithm_object.compute_prediction(request.data)
#
#
#         label = prediction["label"] if "label" in prediction else "error"
#         ml_request = VMLRequest(
#             input_data=json.dumps(request.data),
#             full_response=prediction,
#             response=label,
#             feedback="",
#             parent_mlalgorithm=algs[alg_index],
#         )
#         ml_request.save()
#
#         prediction["request_id"] = ml_request.id
#
#         return Response(prediction)

class VPredictView(views.APIView):
    def post(self, request, vendpoint_name,format=None):
        algorithm_status = self.request.query_params.get("status", "production")
        algorithm_version = self.request.query_params.get("version")

        algs = VMLAlgorithm.objects.filter(parent_endpoint__name = vendpoint_name, status__status = algorithm_status, status__active=True)

        if algorithm_version is not None:
            algs = algs.filter(version = algorithm_version)

        if len(algs) == 0:
            return Response(
                {"status": "Error", "message": "ML algorithm is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(algs) != 1 and algorithm_status != "ab_testing":
            return Response(
                {"status": "Error", "message": "ML algorithm selection is ambiguous. Please specify algorithm version."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alg_index = 0
        if algorithm_status == "ab_testing":
            alg_index = 0 if rand() < 0.5 else 1

        algorithm_object = mmpose_registry.VMLAlgorithms[algs[alg_index].id]
        inputvideopath = os.path.join(globalsettings.BASE_DIR,urlsplit(request.data['inputvideopath']).path[1:]).replace('\\', '/')
        prediction = algorithm_object.pose_inference(inputvideopath)

        res_json_data = json.loads(prediction)
        pred_save_path =  f'{globalsettings.POSE_RESULT_PATH}/results_' \
                              f'{os.path.splitext(os.path.basename(inputvideopath))[0]}.json'

        if not os.path.exists(globalsettings.POSE_RESULT_PATH):
            os.makedirs(globalsettings.POSE_RESULT_PATH)

        with open(pred_save_path, 'w') as json_file:
            json.dump(res_json_data, json_file, indent=4)

       # label = prediction["label"] if "label" in prediction else "error"
        ml_request = VMLRequest(
            input_data=inputvideopath,
            full_response=pred_save_path,
            response=pred_save_path,
            feedback="",
            parent_mlalgorithm=algs[alg_index],
        )
        ml_request.save()

        #prediction["request_id"] = ml_request.id

        return Response(pred_save_path)

