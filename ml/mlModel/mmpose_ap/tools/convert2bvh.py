from .camera import  *
import  os
from .bvh_skeleton import h36m_skeleton,smartbody_skeleton
import pickle
import numpy as np

def rotationAddRoll(R,roll_to_add):
     # 要添加的 roll 轴旋转角度，单位为度

    # 将旋转矩阵 R 分解为欧拉角
    roll, pitch, yaw = np.degrees(np.arctan2(R[2, 1], R[2, 2])), np.degrees(
        np.arctan2(-R[2, 0], np.sqrt(R[2, 1] ** 2 + R[2, 2] ** 2))), np.degrees(np.arctan2(R[1, 0], R[0, 0]))

    # 将 roll 轴的旋转角度加到当前的 roll 角度上
    yaw += roll_to_add

    # 限制 roll 角度的范围在 -180 到 180 度之间
    yaw = (roll + 180) % 360 - 180

    # 使用更新后的欧拉角重新构造旋转矩阵
    roll_rad, pitch_rad, yaw_rad = np.radians(roll), np.radians(pitch), np.radians(yaw)
     # 构造绕 Z 轴的旋转矩阵
    R_x = np.array([[np.cos(yaw_rad), -np.sin(yaw_rad), 0],
                     [np.sin(yaw_rad), np.cos(yaw_rad), 0],
                     [0, 0, 1]])

     # 构造绕 Y 轴的旋转矩阵
    R_z = np.array([[np.cos(pitch_rad), 0, np.sin(pitch_rad)],
                     [0, 1, 0],
                     [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]])

     # 构造绕 X 轴的旋转矩阵
    R_y = np.array([[1, 0, 0],
                     [0, np.cos(roll_rad), -np.sin(roll_rad)],
                     [0, np.sin(roll_rad), np.cos(roll_rad)]])

     # 将每个旋转矩阵相乘以获得最终的旋转矩阵
    R_adjusted = np.dot(R_z, np.dot(R_y, R_x))
    return R_adjusted
def convertResH36m2bvh(prediction3d,viz_output):
    # 第三步：将预测的三维点从相机坐标系转换到世界坐标系
    # （1）第一种转换方法
    # rot = np.array([0.14070565, -0.15007018, -0.7552408, 0.62232804], dtype=np.float64)
    # #rot = np.array([0, 0, 0, 0], dtype=np.float32)
    # prediction = camera_to_world(prediction3d, R=rot, t=0)
    # #prediction = camera2world(pose=prediction3d, R=rot, T=0)
    # # We don't have the trajectory, but at least we can rebase the height将预测的三维点的Z值减去预测的三维点中Z的最小值，得到正向的Z值
    # prediction[:, :, 2] -= np.min(prediction[:, :, 2])

    # （2）第二种转换方法
    subject = 'S9'
    cam_id = '55011271'
    #cam_params = load_camera_params('ml/mlModel/mmpose_ap/tools/cameras.h5')[subject][cam_id]
    cam_params = load_camera_params_pkl('D:/AI/Datasets/h36m/human36m/processed/annotation_body3d/cameras.pkl')[subject,cam_id]
    R = cam_params['R']
    T = cam_params['T']/cam_params['w']
    #azimuth = cam_params['azimuth']
    azimuth = {
        '54138969': 70, '55011271': -0.4, '58860488': 110, '60457274': -100
    }
    R_x = np.array([[np.cos(azimuth[cam_id]), -np.sin(azimuth[cam_id]), 0],
                    [np.sin(azimuth[cam_id]), np.cos(azimuth[cam_id]), 0],
                    [0, 0, 1]])

    R_y = np.array([[1, 0, 0],
                    [0, np.cos(azimuth[cam_id]), -np.sin(azimuth[cam_id])],
                    [0, np.sin(azimuth[cam_id]), np.cos(azimuth[cam_id])]])
    R_z = np.array([[np.cos(azimuth[cam_id]), 0, np.sin(azimuth[cam_id])],
                    [0, 1, 0],
                    [-np.sin(azimuth[cam_id]), 0, np.cos(azimuth[cam_id])]])
    R_adjusted = np.dot(R_x ,R)    #rotationAddRoll(R,70)

    prediction = camera2world(pose=prediction3d, R=R_adjusted, T=T)
    prediction[:, :, 2] -= (np.min(prediction[:, :, 2])) # rebase the height

    # 第四步：将3D关键点输出并将预测的3D点转换为bvh骨骼
    # 将三维预测点输出
#    write_3d_point( viz_output,prediction)

    # 将预测的三维骨骼点转换为bvh骨骼
    prediction_copy = np.copy(prediction)
    bvhfile = write_standard_bvh(viz_output,prediction_copy) #转为标准bvh骨骼
    #bvhfile=write_smartbody_bvh(viz_output,prediction_copy) #转为SmartBody所需的bvh骨骼
    return bvhfile

def write_3d_point(outvideopath,prediction3dpoint):
    '''
    :param prediction3dpoint: 预测的三维字典
    :param outfilepath: 输出的三维点的文件
    :return:
    '''
    dir_name = os.path.dirname(outvideopath)
    basename = os.path.basename(outvideopath)
    video_name = basename[:basename.rfind('.')]

    frameNum = 1

    for frame in prediction3dpoint:
        outfileDirectory = os.path.join(dir_name,video_name,"3dpoint");
        if not os.path.exists(outfileDirectory):
            os.makedirs(outfileDirectory)
        outfilename = os.path.join(dir_name,video_name,"3dpoint","3dpoint{}.txt".format(frameNum))
        file = open(outfilename, 'w')
        frameNum += 1
        for point3d in frame:
            # （1）转换成SmartBody和Meshlab的坐标系，Y轴向上，X向右，Z轴向前
            # X = point3d[0]
            # Y = point3d[1]
            # Z = point3d[2]
            #
            # X_1 = -X
            # Y_1 = Z
            # Z_1 = Y
            # str = '{},{},{}\n'.format(X_1, Y_1, Z_1)

            #（2）未转换任何坐标系的输出，Z轴向上，X向右，Y向前
            str = '{},{},{}\n'.format(point3d[0],point3d[1],point3d[2])
            file.write(str)
        file.close()

# 将3dpoint转换为标准的bvh格式并输出到outputs/outputvideo/alpha_pose_视频名/bvh下
def write_standard_bvh(outbvhfilepath,prediction3dpoint):
    '''
    :param outbvhfilepath: 输出bvh动作文件路径
    :param prediction3dpoint: 预测的三维关节点
    :return:
    '''

    # 将预测的点放大100倍
    for frame in prediction3dpoint:
        for point3d in frame:
            point3d[0] *= 100
            point3d[1] *= 100
            point3d[2] *= 100

            # 交换Y和Z的坐标
            X = point3d[0]
            Y = point3d[1]
            Z = point3d[2]

            point3d[0] = -X
            # point3d[1] = Z
            # point3d[2] = Y

    dir_name = os.path.dirname(outbvhfilepath)
    basename = os.path.basename(outbvhfilepath)
    video_name = basename[:basename.rfind('.')]
    bvhfileDirectory = os.path.join(dir_name,video_name,"bvh")
    if not os.path.exists(bvhfileDirectory):
        os.makedirs(bvhfileDirectory)
    bvhfileName = os.path.join(dir_name,video_name,"bvh","{}.bvh".format(video_name))
    human36m_skeleton = h36m_skeleton.H36mSkeleton()
    human36m_skeleton.poses2bvh(prediction3dpoint,output_file=bvhfileName)
    return bvhfileName

# 将3dpoint转换为SmartBody的bvh格式并输出到outputs/outputvideo/alpha_pose_视频名/bvh下
def write_smartbody_bvh(outbvhfilepath,prediction3dpoint):
    '''
    :param outbvhfilepath: 输出bvh动作文件路径
    :param prediction3dpoint: 预测的三维关节点
    :return:
    '''

    # 将预测的点放大100倍
    for frame in prediction3dpoint:
        for point3d in frame:
            point3d[0] *= 100
            point3d[1] *= 100
            point3d[2] *= 100

            # 交换Y和Z的坐标
            X = point3d[0]
            Y = point3d[1]
            Z = point3d[2]

            point3d[0] = -X
            # point3d[1] = Z
            # point3d[2] = Y

    dir_name = os.path.dirname(outbvhfilepath)
    basename = os.path.basename(outbvhfilepath)
    video_name = basename[:basename.rfind('.')]
    bvhfileDirectory = os.path.join(dir_name,video_name,"bvh")
    if not os.path.exists(bvhfileDirectory):
        os.makedirs(bvhfileDirectory)
    bvhfileName = os.path.join(dir_name,video_name,"bvh","{}.bvh".format(video_name))

    SmartBody_skeleton = smartbody_skeleton.SmartBodySkeleton()
    SmartBody_skeleton.poses2bvh(prediction3dpoint,output_file=bvhfileName)
    return bvhfileName