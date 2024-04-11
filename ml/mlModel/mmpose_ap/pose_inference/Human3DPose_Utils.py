import numpy as np
from functools import partial
from mmengine.structures import InstanceData
from mmpose.structures import (PoseDataSample, merge_data_samples,
                               split_instances)

from ml.mlModel.mmpose_ap.mmpose.post_processing.smoother import Smoother
from typing import Dict
try:
    from mmdet.apis import inference_detector, init_detector
    has_mmdet = True
except (ImportError, ModuleNotFoundError):
    has_mmdet = False
def get_area(results):
    for i, data_sample in enumerate(results):
        pred_instance = data_sample.pred_instances.cpu().numpy()
        if 'bboxes' in pred_instance:
            bboxes = pred_instance.bboxes
            results[i].pred_instances.set_field(
                np.array([(bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                          for bbox in bboxes]), 'areas')
        else:
            keypoints = pred_instance.keypoints
            areas, bboxes = [], []
            for keypoint in keypoints:
                xmin = np.min(keypoint[:, 0][keypoint[:, 0] > 0], initial=1e10)
                xmax = np.max(keypoint[:, 0])
                ymin = np.min(keypoint[:, 1][keypoint[:, 1] > 0], initial=1e10)
                ymax = np.max(keypoint[:, 1])
                areas.append((xmax - xmin) * (ymax - ymin))
                bboxes.append([xmin, ymin, xmax, ymax])
            results[i].pred_instances.areas = np.array(areas)
            results[i].pred_instances.bboxes = np.array(bboxes)
    return results

from mmpose.apis import (_track_by_iou, _track_by_oks, collect_multi_frames,
                         convert_keypoint_definition, extract_pose_sequence,
                         inference_pose_lifter_model, inference_topdown,
                         init_model)
def get_pose_est_results(args, pose_estimator, frame, bboxes,
                         pose_est_results_last, next_id, pose_lift_dataset):
    pose_det_dataset = pose_estimator.cfg.test_dataloader.dataset

    # make person results for current image
    pose_est_results = inference_topdown(pose_estimator, frame, bboxes)

    pose_est_results = get_area(pose_est_results)
    if args.use_oks_tracking:
        _track = partial(_track_by_oks)
    else:
        _track = _track_by_iou

    for i, result in enumerate(pose_est_results):
        track_id, pose_est_results_last, match_result = _track(
            result, pose_est_results_last, args.tracking_thr)
        if track_id == -1:
            pred_instances = result.pred_instances.cpu().numpy()
            keypoints = pred_instances.keypoints
            if np.count_nonzero(keypoints[:, :, 1]) >= 3:
                pose_est_results[i].set_field(next_id, 'track_id')
                next_id += 1
            else:
                # If the number of keypoints detected is small,
                # delete that person instance.
                keypoints[:, :, 1] = -10
                pose_est_results[i].pred_instances.set_field(
                    keypoints, 'keypoints')
                bboxes = pred_instances.bboxes * 0
                pose_est_results[i].pred_instances.set_field(bboxes, 'bboxes')
                pose_est_results[i].set_field(-1, 'track_id')
                pose_est_results[i].set_field(pred_instances, 'pred_instances')
        else:
            pose_est_results[i].set_field(track_id, 'track_id')

        del match_result

    pose_est_results_converted = []
    for pose_est_result in pose_est_results:
        pose_est_result_converted = PoseDataSample()
        gt_instances = InstanceData()
        pred_instances = InstanceData()
        for k in pose_est_result.gt_instances.keys():
            gt_instances.set_field(pose_est_result.gt_instances[k], k)
        for k in pose_est_result.pred_instances.keys():
            pred_instances.set_field(pose_est_result.pred_instances[k], k)
        pose_est_result_converted.gt_instances = gt_instances
        pose_est_result_converted.pred_instances = pred_instances
        pose_est_result_converted.track_id = pose_est_result.track_id

        keypoints = convert_keypoint_definition(pred_instances.keypoints,
                                                pose_det_dataset['type'],
                                                pose_lift_dataset['type'])
        pose_est_result_converted.pred_instances.keypoints = keypoints
        pose_est_results_converted.append(pose_est_result_converted)
    return pose_est_results, pose_est_results_converted, next_id

def get_pose_lift_results(args, visualizer, pose_lifter, pose_est_results_list,
                          frame, frame_idx, pose_est_results,keypoints3Dpos):
    pose_lift_dataset = pose_lifter.cfg.test_dataloader.dataset
    # extract and pad input pose2d sequence
    pose_seq_2d = extract_pose_sequence(
        pose_est_results_list,
        frame_idx=frame_idx,
        causal=pose_lift_dataset.get('causal', False),
        seq_len=pose_lift_dataset.get('seq_len', 1),
        step=pose_lift_dataset.get('seq_step', 1))

    # 2D-to-3D pose lifting
    width, height = frame.shape[:2]
    pose_lift_results = inference_pose_lifter_model(
        pose_lifter,
        pose_seq_2d,
        image_size=(width, height),
        norm_pose_2d=args.norm_pose_2d)

    # Pose processing
    for idx, pose_lift_res in enumerate(pose_lift_results):
        pose_lift_res.track_id = pose_est_results[idx].get('track_id', 1e4)

        pred_instances = pose_lift_res.pred_instances
        keypoints = pred_instances.keypoints
        keypoint_scores = pred_instances.keypoint_scores
        if keypoint_scores.ndim == 3:
            keypoint_scores = np.squeeze(keypoint_scores, axis=1)
            pose_lift_results[
                idx].pred_instances.keypoint_scores = keypoint_scores
        if keypoints.ndim == 4:
            keypoints = np.squeeze(keypoints, axis=1)

        keypoints = keypoints[..., [0, 2, 1]]
        keypoints[..., 0] = -keypoints[..., 0]
        keypoints[..., 2] = -keypoints[..., 2]

        # rebase height (z-axis)
        if args.rebase_keypoint_height:
            keypoints[..., 2] -= np.min(
                keypoints[..., 2], axis=-1, keepdims=True)

        pose_lift_results[idx].pred_instances.keypoints = keypoints

    pose_lift_results = sorted(
        pose_lift_results, key=lambda x: x.get('track_id', 1e4))

    pred_3d_data_samples = merge_data_samples(pose_lift_results)
    det_data_sample = merge_data_samples(pose_est_results)

    pred_3d_instances = pred_3d_data_samples.get('pred_instances', None)
    for idx, pred_3d_instance in enumerate(pred_3d_instances):
        keypoints = pred_3d_instance.keypoints
        keypoints3Dpos.append(
            keypoints[0]
        )


    if args.num_instances < 0:
        args.num_instances = len(pose_lift_results)

    # Visualization
    # if visualizer is not None:
    #     visualizer.add_datasample(
    #         'result',
    #         frame,
    #         data_sample=pred_3d_data_samples,
    #         det_data_sample=det_data_sample,
    #         draw_gt=False,
    #         show=args.show,
    #         draw_bbox=True,
    #         kpt_thr=args.kpt_thr,
    #         num_instances=args.num_instances,
    #         wait_time=args.show_interval)

    return pred_3d_data_samples.get('pred_instances', None)


def get_bbox(args, detector, frame):
    det_result = inference_detector(detector, frame)
    pred_instance = det_result.pred_instances.cpu().numpy()

    bboxes = pred_instance.bboxes
    bboxes = bboxes[np.logical_and(pred_instance.labels == args.det_cat_id,
                                   pred_instance.scores > args.bbox_thr)]
    return bboxes
def display_model_aliases(model_aliases: Dict[str, str]) -> None:
    """Display the available model aliases and their corresponding model
    names."""
    aliases = list(model_aliases.keys())
    max_alias_length = max(map(len, aliases))
    print(f'{"ALIAS".ljust(max_alias_length+2)}MODEL_NAME')
    for alias in sorted(aliases):
        print(f'{alias.ljust(max_alias_length+2)}{model_aliases[alias]}')


def smoother_pose(keypoints):
     # Build dummy pose result
    results = []
    for keypoint in keypoints:
        results_t = []
        for track_id in range(1):
            result = {
                              'track_id': 0,
                'keypoints': keypoint
                                  }
            results_t.append(result)
        results.append(results_t)
    # Example 1: Smooth multi-frame pose results offline.
    # filter_cfg = dict(type='GaussianFilter', window_size=3)
    # smoother = Smoother(filter_cfg, keypoint_dim=2)
    # smoothed_results = smoother.smooth(results)
    # Example 2: Smooth pose results online frame-by-frame
    smoothed_results = []
    filter_cfg = dict(type='GaussianFilter', window_size=3)
    smoother = Smoother(filter_cfg, keypoint_dim=2)
    for result_t in results:
        smoothed_result = smoother.smooth(result_t)
        smoothed_results.append(smoothed_result)
    return smoothed_results