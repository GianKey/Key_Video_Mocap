from .camera import  *
import  os
from .bvh_skeleton import h36m_skeleton,smartbody_skeleton
def convertResH36m2bvh(prediction3d,viz_output):
    # 第三步：将预测的三维点从相机坐标系转换到世界坐标系
    # （1）第一种转换方法
    rot = np.array([0.14070565, -0.15007018, -0.7552408, 0.62232804], dtype=np.float32)
    #rot = np.array([0, 0, 0, 0], dtype=np.float32)
    prediction = camera_to_world(prediction3d, R=rot, t=0)
    # We don't have the trajectory, but at least we can rebase the height将预测的三维点的Z值减去预测的三维点中Z的最小值，得到正向的Z值
    prediction[:, :, 2] -= np.min(prediction[:, :, 2])

    # （2）第二种转换方法
    # subject = 'S1'
    # cam_id = '55011271'
    # cam_params = load_camera_params('ml/mlModel/mmpose_ap/tools/cameras.h5')[subject][cam_id]
    # R = cam_params['R']
    # T = 0
    # azimuth = cam_params['azimuth']
    #
    # prediction = camera2world(pose=prediction3d, R=R, T=T)
    # prediction[:, :, 2] -= (np.min(prediction[:, :, 2])) # rebase the height

    # 第四步：将3D关键点输出并将预测的3D点转换为bvh骨骼
    # 将三维预测点输出
    write_3d_point( viz_output,prediction)

    # 将预测的三维骨骼点转换为bvh骨骼
    prediction_copy = np.copy(prediction)
    bvhfile = write_standard_bvh(viz_output,prediction_copy) #转为标准bvh骨骼
    bvhfile=write_smartbody_bvh(viz_output,prediction_copy) #转为SmartBody所需的bvh骨骼
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
            #X = point3d[0]
            #Y = point3d[1]
            #Z = point3d[2]

            #point3d[0] = -X
            #point3d[1] = Z
            #point3d[2] = Y

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
            # point3d[0] *= 100
            # point3d[1] *= 100
            # point3d[2] *= 100

            # 交换Y和Z的坐标
            X = point3d[0]
            Y = point3d[1]
            Z = point3d[2]

            point3d[0] = -X
            point3d[1] = Z
            point3d[2] = Y

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