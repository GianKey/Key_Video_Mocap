from mmdeploy.apis.utils import build_task_processor
from mmdeploy.utils import get_input_shape, load_config
import torch

deploy_cfg = '../mmdeploy/configs/mmpose/pose-detection_onnxruntime_static.py'
model_cfg = 'td-hm_hrnet-w48_8xb32-210e_coco-256x192.py'

device = 'cpu'
backend_model = ['F:/AI/BackEnd/AIBackEnd/mmpose_backend/mmdeploy_models/ort/pd_static_end2end.onnx']
image = '../demo/resources/laufey.png'

# read deploy_cfg and model_cfg
deploy_cfg, model_cfg = load_config(deploy_cfg, model_cfg)

# build task and backend model
task_processor = build_task_processor(model_cfg, deploy_cfg, device)
model = task_processor.build_backend_model(backend_model)

# process input image
input_shape = get_input_shape(deploy_cfg)
model_inputs, _ = task_processor.create_input(image, input_shape)

# do model inference
with torch.no_grad():
    result = model.test_step(model_inputs)

# visualize results
task_processor.visualize(
    image=image,
    model=model,
    result=result[0],
    window_name='visualize',
    output_file='vis_results/output_laufey_pose.png')