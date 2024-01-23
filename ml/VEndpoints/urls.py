from django.conf.urls import  include
from django.urls import  re_path as url
from rest_framework.routers import DefaultRouter

from ml.VEndpoints.views import VEndpointViewSet
from ml.VEndpoints.views import VMLAlgorithmViewSet
from ml.VEndpoints.views import VMLAlgorithmStatusViewSet
from ml.VEndpoints.views import VMLRequestViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"vendpoints", VEndpointViewSet, basename="vendpoints")
router.register(r"vmlalgorithms", VMLAlgorithmViewSet, basename="vmlalgorithms")
router.register(r"vmlalgorithmstatuses", VMLAlgorithmStatusViewSet, basename="vmlalgorithmstatuses")
router.register(r"vmlrequests", VMLRequestViewSet, basename="vmlrequests")

urlpatterns = [
   url(r"^vml/", include(router.urls)),
]
