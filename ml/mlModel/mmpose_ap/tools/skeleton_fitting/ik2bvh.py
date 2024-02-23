from pathlib import Path
from ml.mlModel.mmpose_ap.tools.bvh_skeleton.bvh_helper import BvhNode,BvhHeader
from ml.mlModel.mmpose_ap.tools.skeleton_fitting.ik.BVH import load
from ml.mlModel.mmpose_ap.tools.camera import  *
import  os

class H36mSkeleton2(object):
    def __init__(self):
        self.root = 'Hip'
        self.keypoint2index = {
            'Hip': 0,
            'RightHip': 1,
            'RightKnee': 2,
            'RightAnkle': 3,
            'LeftHip': 4,
            'LeftKnee': 5,
            'LeftAnkle': 6,
            'Spine': 7,
            'Neck': 8,
            'Nose': 9,
            'Head': 10,
            'LeftShoulder': 11,
            'LeftElbow': 12,
            'LeftWrist': 13,
            'RightShoulder': 14,
            'RightElbow': 15,
            'RightWrist': 16,
            'Thorax': 17,
            'RightAnkleEndSite': -1,
            'LeftAnkleEndSite': -1,
            'LeftWristEndSite': -1,
            'RightWristEndSite': -1,
            'HeadEndSite': -1,
            'NoseEndSite': -1,
        }
        self.children = {
            'Hip': ['RightHip', 'LeftHip', 'Spine'],
            'RightHip': ['RightKnee'],
            'RightKnee': ['RightAnkle'],
            'RightAnkle': ['RightAnkleEndSite'],
            'RightAnkleEndSite': [],
            'LeftHip': ['LeftKnee'],
            'LeftKnee': ['LeftAnkle'],
            'LeftAnkle': ['LeftAnkleEndSite'],
            'LeftAnkleEndSite': [],
            'Spine': ['Thorax'],
            'Thorax': ['Neck', 'LeftShoulder', 'RightShoulder', 'Nose'],
            'Neck': ['Head'],
            'Head': ['HeadEndSite'],
            'HeadEndSite': [],  # Head is an end site
            'LeftShoulder': ['LeftElbow'],
            'LeftElbow': ['LeftWrist'],
            'LeftWrist': ['LeftWristEndSite'],
            'LeftWristEndSite': [],
            'RightShoulder': ['RightElbow'],
            'RightElbow': ['RightWrist'],
            'RightWrist': ['RightWristEndSite'],
            'RightWristEndSite': [],
            'NoseEndSite': [],
            'Nose': ['NoseEndSite']
        }
        # human3.6m坐标系(Z向上，Y向前，X向左)下的T-pose
        self.initial_directions = {
            'Hip': [0, 0, 0],
            'RightHip': [-1, 0, 0],
            'RightKnee': [0, 0, -1],
            'RightAnkle': [0, 0, -1],
            'RightAnkleEndSite': [0, -1, 0],
            'LeftHip': [1, 0, 0],
            'LeftKnee': [0, 0, -1],
            'LeftAnkle': [0, 0, -1],
            'LeftAnkleEndSite': [0, -1, 0],
            'Spine': [0, 0, 1],
            'Thorax': [0, 0, 1],
            'Neck': [0, 0, 1],
            'Nose': [0, 0, 1],
            'Head': [0, 0, 1],
            'LeftShoulder': [1, 0, 0],
            'LeftElbow': [1, 0, 0],
            'LeftWrist': [1, 0, 0],
            'LeftWristEndSite': [1, 0, 0],
            'RightShoulder': [-1, 0, 0],
            'RightElbow': [-1, 0, 0],
            'RightWrist': [-1, 0, 0],
            'RightWristEndSite': [-1, 0, 0],
            'HeadEndSite': [-1, 0, 0],
            'NoseEndSite': [-1, 0, 0],
        }

        self.idx2name = ['root', 'R-hip',
                         'R-knee', 'R-ankle',
                         'L-hip', 'L-knee',
                         'L-ankle', 'torso',
                         'neck', 'nose',
                         'head', 'L-shoulder',
                         'L-elbow', 'L-wrist',
                         'R-shoulder', 'R-elbow',
                         'R-wrist', 'thorax']

        self.parent = {self.root: None}
        for parent, children in self.children.items():
            for child in children:
                self.parent[child] = parent

        self.left_joints = [
            joint for joint in self.keypoint2index
            if 'Left' in joint
        ]
        self.right_joints = [
            joint for joint in self.keypoint2index
            if 'Right' in joint
        ]

    def get_initial_offset(self, poses_3d):
            # TODO: RANSAC
            bone_lens = {self.root: [1]}
            stack = [self.root]
            while stack:
                parent = stack.pop()
                p_idx = self.keypoint2index[parent]
                for child in self.children[parent]:
                    if 'EndSite' in child:
                        bone_lens[child] = 0.4 * bone_lens[parent]
                        continue
                    stack.append(child)

                    c_idx = self.keypoint2index[child]
                    bone_lens[child] = np.linalg.norm(
                        poses_3d[:, p_idx] - poses_3d[:, c_idx],
                        axis=1
                    )

            bone_len = {}
            for joint in self.keypoint2index:
                if 'Left' in joint or 'Right' in joint:
                    base_name = joint.replace('Left', '').replace('Right', '')
                    left_len = np.mean(bone_lens['Left' + base_name])
                    right_len = np.mean(bone_lens['Right' + base_name])
                    bone_len[joint] = (left_len + right_len) / 2
                else:
                    bone_len[joint] = np.mean(bone_lens[joint])

            initial_offset = {}
            for joint, direction in self.initial_directions.items():
                direction = np.array(direction) / max(np.linalg.norm(direction), 1e-12)
                initial_offset[joint] = direction * bone_len[joint]

            return initial_offset

    def get_bvh_header(self, poses_3d):
            initial_offset = self.get_initial_offset(poses_3d)

            nodes = {}
            for joint in self.keypoint2index:
                is_root = joint == self.root
                is_end_site = 'EndSite' in joint
                nodes[joint] = BvhNode(
                    name=joint,
                    offset=initial_offset[joint],
                    rotation_order='xyz' if not is_end_site else '',
                    is_root=is_root,
                    is_end_site=is_end_site,
                )
            for joint, children in self.children.items():
                nodes[joint].children = [nodes[child] for child in children]
                for child in children:
                    nodes[child].parent = nodes[joint]

            header = BvhHeader(root=nodes[self.root], nodes=nodes)
            return header

    def pose2pos(self, pose, header):
            channel = []
            #positions = {}
            stack = [header.root]
            while stack:
                node = stack.pop()
                joint = node.name
                joint_idx = self.keypoint2index[joint]

                # if node.is_root:
                #     channel.extend(pose[joint_idx])

                # index = keypoint2index

                #positions[joint] = pose[joint_idx]
                channel.extend(pose[joint_idx])

                for child in node.children[::-1]:
                    if not child.is_end_site:
                        stack.append(child)

            return channel

    def poses2bvh(self,poses_3d, header=None, output_file=None):
            if not header:
                header = self.get_bvh_header(poses_3d)

            channels = []
            for frame, pose in enumerate(poses_3d):
                channels.append(self.pose2pos(pose, header))
                # channels.append(self.pose2euler_SmartBody(pose, header))
                # channels.append(self.pose2euler_SmartBody_Modify(pose, header))

            if output_file:
                write_bvh(output_file, header, channels)

            return channels, header



def write_header(writer, node, level):
    indent = ' ' * 4 * level
    if node.is_root:
        writer.write(f'{indent}ROOT {node.name}\n')
        channel_num = 3
    elif node.is_end_site:
        writer.write(f'{indent}End Site\n')
        channel_num = 0
    else:
        writer.write(f'{indent}JOINT {node.name}\n')
        channel_num = 3
    writer.write(f'{indent}{"{"}\n')

    indent = ' ' * 4 * (level + 1)
    writer.write(
        f'{indent}OFFSET '
        f'{node.offset[0]} {node.offset[1]} {node.offset[2]}\n'
    )
    if channel_num:
        channel_line = f'{indent}CHANNELS {channel_num} '
        if node.is_root:
            channel_line += f'Xposition Yposition Zposition '
        else:
            channel_line += ' '.join([
            f'{axis.upper()}position '
            for axis in node.rotation_order
        ])
        writer.write(channel_line + '\n')

    for child in node.children:
        write_header(writer, child, level + 1)

    indent = ' ' * 4 * level
    writer.write(f'{indent}{"}"}\n')



def write_bvh(output_file, header, channels, frame_rate=30):
    output_file = Path(output_file)
    if not output_file.parent.exists():
        os.makedirs(output_file.parent)

    with output_file.open('w') as f:
        f.write('HIERARCHY\n')
        write_header(writer=f, node=header.root, level=0)

        f.write('MOTION\n')
        f.write(f'Frames: {len(channels)}\n')
        f.write(f'Frame Time: {1 / frame_rate}\n')

        for channel in channels:
            f.write(' '.join([f'{element}' for element in channel]) + '\n')



def convertResPose_H36m2bvh(prediction3d,viz_output):
    # 第三步：将预测的三维点从相机坐标系转换到世界坐标系
    # （1）第一种转换方法
    # rot = np.array([0.14070565, -0.15007018, -0.7552408, 0.62232804], dtype=np.float64)
    # #rot = np.array([0, 0, 0, 0], dtype=np.float32)
    # prediction = camera_to_world(prediction3d, R=rot, t=0)
    # #prediction = camera2world(pose=prediction3d, R=rot, T=0)
    # # We don't have the trajectory, but at least we can rebase the height将预测的三维点的Z值减去预测的三维点中Z的最小值，得到正向的Z值
    # prediction[:, :, 2] -= np.min(prediction[:, :, 2])

    # （2）第二种转换方法
    subject = 'S1'
    cam_id = '55011271'
    cam_params = load_camera_params('D:/Project/Internet/Django/key_video/Key_Video_Mocap/Key_Video_Mocap/ml/mlModel/mmpose_ap/tools/cameras.h5')[subject][cam_id]
    R = cam_params['R']
    T = 0
    azimuth = cam_params['azimuth']

    prediction = camera2world(pose=prediction3d, R=R, T=T)
    prediction[:, :, 2] -= (np.min(prediction[:, :, 2])) # rebase the height

    # 第四步：将3D关键点输出并将预测的3D点转换为bvh骨骼
    # 将三维预测点输出
#    write_3d_point( viz_output,prediction)

    # 将预测的三维骨骼点转换为bvh骨骼
    prediction_copy = np.copy(prediction3d)
    #bvhfile = write_standard_bvh(viz_output,prediction_copy) #转为标准bvh骨骼
    bvhfile=write_standard_bvh(viz_output,prediction_copy) #转为SmartBody所需的bvh骨骼
    return bvhfile
def write_standard_bvh(outbvhfilepath,prediction3dpoint):
    '''
    :param outbvhfilepath: 输出bvh动作文件路径
    :param prediction3dpoint: 预测的三维关节点
    :return:
    '''

    # 将预测的点放大100倍
    # for frame in prediction3dpoint:
    #     for point3d in frame:
    #         point3d[0] *= 100
    #         point3d[1] *= 100
    #         point3d[2] *= 100
    #
    #         # 交换Y和Z的坐标
    #         #X = point3d[0]
    #         #Y = point3d[1]
    #         #Z = point3d[2]
    #
    #         #point3d[0] = -X
    #         #point3d[1] = Z
    #         #point3d[2] = Y

    dir_name = os.path.dirname(outbvhfilepath)
    basename = os.path.basename(outbvhfilepath)
    video_name = basename[:basename.rfind('.')]
    bvhfileDirectory = os.path.join(dir_name,video_name,"bvh")
    if not os.path.exists(bvhfileDirectory):
        os.makedirs(bvhfileDirectory)
    bvhfileName = os.path.join(dir_name,video_name,"bvh","{}.bvh".format(video_name))
    human36m_skeleton = H36mSkeleton2()
    human36m_skeleton.poses2bvh(prediction3dpoint,output_file=bvhfileName)
    return bvhfileName

def main():
    #animation, names, frametime = load('ybot.bvh')
    animation, names, frametime = load('D:/Project/Internet/Django/key_video/Key_Video_Mocap/Key_Video_Mocap/pose_result/7fdad48bf7024d7580d0c4d680c2a691/bvh/7fdad48bf7024d7580d0c4d680c2a691.bvh')
    convertResPose_H36m2bvh(animation.positions,'./convert2Bh')

    print('load end')


import pickle
import numpy as np

if __name__ == '__main__':


    f = open('D:/BaiduNetdiskDownload/h36m_validation.pkl', 'rb')
    data = pickle.load(f)
    print(data)
    #main()
