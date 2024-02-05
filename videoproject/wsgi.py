"""
WSGI config for dj_demo_one project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoproject.settings')

application = get_wsgi_application()

import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
application = get_wsgi_application()

# ML registry
import inspect
from ml.mlModel.registry import MLRegistry,MMPoseRegistry
from ml.mlModel.income_classifier.random_forest import RandomForestClassifier
from ml.mlModel.mmpose_ap.pose_inference.pose_inference import Body3dPoseEstimation,Body3dVideoPoseEstimation

try:
    registry = MLRegistry() # create ML registry
    # Random Forest classifier
    rf = RandomForestClassifier()
    # add to ML registry
    registry.add_algorithm(endpoint_name="income_classifier",
                            algorithm_object=rf,
                            algorithm_name="random forest",
                            algorithm_status="production",
                            algorithm_version="0.0.1",
                            owner="Piotr",
                            algorithm_description="Random Forest with simple pre- and post-processing",
                            algorithm_code=inspect.getsource(RandomForestClassifier))

except Exception as e:
    print("Exception while loading the algorithms to the registry,", str(e))

#
# try:
#     mmpose_registry = MMPoseRegistry() # create ML registry
#     pi = Body3dPoseEstimation()
#     # add to ML registry
#     mmpose_registry.add_algorithm(endpoint_name="video_mocap",
#                             algorithm_object=pi,
#                             algorithm_name="Body3dPoseEstimation",
#                             algorithm_status="production",
#                             algorithm_version="0.0.1",
#                             owner="Key",
#                             algorithm_description="pose inference for video",
#                             algorithm_code=inspect.getsource(Body3dPoseEstimation),
#                                   active=False)
#
# except Exception as e:
#     print("Exception while loading the algorithms to the registry,", str(e))


try:
    mmpose_registry = MMPoseRegistry() # create ML registry
    pi = Body3dVideoPoseEstimation()
    # add to ML registry
    mmpose_registry.add_algorithm(endpoint_name="video_mocap",
                            algorithm_object=pi,
                            algorithm_name="Body3dVideoPoseEstimation",
                            algorithm_status="production",
                            algorithm_version="0.0.1",
                            owner="Key",
                            algorithm_description="pose inference for video",
                            algorithm_code=inspect.getsource(Body3dPoseEstimation),
                            active = True
    )

except Exception as e:
    print("Exception while loading the algorithms to the registry,", str(e))

