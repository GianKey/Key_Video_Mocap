from django.conf.urls import  include
from django.urls import  re_path as url
from rest_framework.routers import DefaultRouter

from ml.endpoints.views import EndpointViewSet ,PredictView
from ml.endpoints.views import MLAlgorithmViewSet
from ml.endpoints.views import MLAlgorithmStatusViewSet
from ml.endpoints.views import MLRequestViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"endpoints", EndpointViewSet, basename="endpoints")
router.register(r"mlalgorithms", MLAlgorithmViewSet, basename="mlalgorithms")
router.register(r"mlalgorithmstatuses", MLAlgorithmStatusViewSet, basename="mlalgorithmstatuses")
router.register(r"mlrequests", MLRequestViewSet, basename="mlrequests")

urlpatterns = [
   url(r"^api/v1/", include(router.urls)),
   url(
        r"^api/v1/(?P<endpoint_name>.+)/predict$", PredictView.as_view(), name="predict"
    ),
]
