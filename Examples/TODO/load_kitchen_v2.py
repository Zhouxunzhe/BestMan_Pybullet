"""
@Description :   Load a specific kitchen environment
@Author      :   Yan Ding 
@Time        :   2024/01/07 16:41:55
"""

import math
import os
import sys

import pybullet as p

"""
Get the utils module path
"""
# customized package
current_path = os.path.abspath(__file__)
utils_path = os.path.dirname(os.path.dirname(current_path)) + "/utils"
if os.path.basename(utils_path) != "utils":
    raise ValueError('Not add the path of folder "utils", please check again!')
sys.path.append(utils_path)
from utils_Bestman import Bestman, Pose
from utils_PbClient import PbClient
from utils_PbOMPL import PbOMPL
from utils_PbVisualizer import PbVisualizer

# load kitchen from three scenarios
index = 2
if index == 0:
    from utils_Kitchen_v0 import Kitchen
elif index == 1:
    from utils_Kitchen_v1 import Kitchen
elif index == 2:
    from utils_Kitchen_v2 import Kitchen
else:
    assert False, "index should be 0, 1 or 2"

# pb_client = PbClient(enable_GUI=True, enable_Debug=True)
pb_client = PbClient(enable_GUI=True)
pb_client.enable_vertical_view(1.0, [2.3, 2.6, 2.3], -90, -75)
pb_visualizer = PbVisualizer(pb_client)
# logID = pb_client.start_record("example_manipulation") # start recording
init_pose = Pose([10, 0, 0], [0.0, 0.0, math.pi / 2])
demo = Bestman(init_pose, pb_client)  # load robot
demo.get_joint_link_info("arm")  # get info about arm
init_joint = [0, -1.57, 2.0, -1.57, -1.57, 0]
demo.move_arm_to_joint_angles(init_joint)  # reset arm joint position

# load kitchen
kitchen = Kitchen(pb_client)
print("object ids in loaded kitchen:\n{}".format(kitchen.object_ids))

# load OMPL planner
threshold_distance = 0.1
ompl = PbOMPL(
    pb_client=pb_client,
    arm_id=demo.arm_id,
    joint_idx=demo.arm_joint_indexs,
    tcp_link=demo.tcp_link,
    obstacles=[],
    planner="RRTConnect",
    threshold=threshold_distance,
)

# add obstacles
ompl.add_scene_obstacles(display=True)
ompl.check_obstacles()

# disconnect pybullet
pb_client.run(100)
pb_client.wait(100)
pb_client.disconnect_pybullet()
