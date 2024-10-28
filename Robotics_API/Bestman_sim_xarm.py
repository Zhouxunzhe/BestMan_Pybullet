# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
# @FileName       : Bestman_sim_xarm.py
# @Time           : 2024-08-03 15:08:13
# @Author         : yk
# @Email          : yangkui1127@gmail.com
# @Description:   : xarm robot
"""

import math
import time

import numpy as np
import pybullet as p
from scipy.spatial.transform import Rotation as R

from .Bestman_sim import Bestman_sim
from .Pose import Pose


class Bestman_sim_xarm(Bestman_sim):
    """
    A class representing a simulation for the Bestman robot equipped with a xarm arm.
    """

    def __init__(self, client, visualizer, cfg):
        """
        Initialize the Bestman_sim_xarm with the given parameters.

        Args:
            client (int): The PyBullet client ID.
            visualizer (bool): Flag indicating whether visualization is enabled.
            cfg (dict): Configuration settings.
        """

        # Init parent class: BestMan_sim
        super().__init__(client, visualizer, cfg)

        # Create a gear constraint to keep the fingers symmetrically centered
        c = p.createConstraint(
            self.arm_id,
            9,
            self.arm_id,
            12,
            jointType=p.JOINT_GEAR,
            jointAxis=[1, 0, 0],
            parentFramePosition=[0, 0, 0],
            childFramePosition=[0, 0, 0]
        )

        # Modify constraint parameters
        p.changeConstraint(c, gearRatio=-1, erp=0.1, maxForce=1000)

        # gripper range
        self.gripper_range = [0, 0.05]

        # close gripper
        self.sim_close_gripper()

    # ----------------------------------------------------------------
    # Functions for arm
    # ----------------------------------------------------------------

    def sim_get_sync_arm_pose(self):
        """
        Get synchronized pose of the robot arm with the base.
        """
        base_pose = self.sim_get_current_base_pose()
        arm_pose = Pose(
            [*base_pose.get_position()[:2], self.arm_place_height],
            base_pose.get_orientation(),
        )
        return arm_pose
        
    # ----------------------------------------------------------------
    # Functions for gripper
    # ----------------------------------------------------------------

    def sim_open_gripper(self):
        """open gripper"""
        self.sim_move_gripper(self.gripper_range[1])
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Gripper open!")

    def sim_close_gripper(self):
        """close gripper"""
        self.sim_move_gripper(self.gripper_range[0])
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Gripper close!")

    def sim_move_gripper(self, open_width):
        """move gripper to special width

        Args:
            open_width (float): gripper open width
        """
        print(f"open_width: {open_width}")
        assert self.gripper_range[0] <= open_width <= self.gripper_range[1]
        for i in [9, 10]:
            p.setJointMotorControl2(
                self.arm_id, i, p.POSITION_CONTROL, open_width, force=100
            )
        self.client.run(30)

    def sim_create_gripper_constraint(self, object, link_id):
        """
        Activate or deactivate the gripper for a movable object.

        Args:
            object (str): The name or ID of the object related to gripper action.
            link_id (int): The ID of the link on the object to be grasped.
            value (int): 0 or 1, where 0 means deactivate (ungrasp) and 1 means activate (grasp).
        """
        object_id = self.client.resolve_object_id(object)

        # cretae constraint
        if self.constraint_id == None:
            link_state = p.getLinkState(object_id, link_id)
            vec_inv, quat_inv = p.invertTransform(link_state[0], link_state[1])
            if self.tcp_link != -1:
                current_pose = self.client.get_object_link_pose(
                    self.arm_id, self.tcp_link
                )
                transform_start_to_link = p.multiplyTransforms(
                    vec_inv,
                    quat_inv,
                    current_pose.get_position(),
                    current_pose.get_orientation(),
                )
                self.constraint_id = p.createConstraint(
                    parentBodyUniqueId=object_id,
                    parentLinkIndex=link_id,
                    childBodyUniqueId=self.arm_id,
                    childLinkIndex=self.tcp_link,
                    jointType=p.JOINT_POINT2POINT,
                    jointAxis=[0, 0, 0],
                    parentFramePosition=transform_start_to_link[0],
                    parentFrameOrientation=transform_start_to_link[1],
                    childFramePosition=[0, 0, 0],
                )
            else:
                current_pose = self.client.get_object_link_pose(
                    self.arm_id, self.eef_id
                )
                transform_start_to_link = p.multiplyTransforms(
                    vec_inv,
                    quat_inv,
                    current_pose.get_position(),
                    current_pose.get_orientation(),
                )
                self.constraint_id = p.createConstraint(
                    parentBodyUniqueId=object_id,
                    parentLinkIndex=link_id,
                    childBodyUniqueId=self.arm_id,
                    childLinkIndex=self.tcp_link,
                    jointType=p.JOINT_POINT2POINT,
                    jointAxis=[0, 0, 0],
                    parentFramePosition=transform_start_to_link[0],
                    parentFrameOrientation=transform_start_to_link[1],
                    childFramePosition=[0, 0, 0],
                )
            p.changeConstraint(self.gripper_id, maxForce=2000)
            self.client.run(40)
            print("[BestMan_Sim][Gripper] Gripper constraint has been created!")

    def sim_remove_gripper_constraint(self):
        """remove constraint"""
        if self.constraint_id != None:
            p.removeConstraint(self.constraint_id, physicsClientId=self.client_id)
            self.client.run(40)
            self.constraint_id = None
            print("[BestMan_Sim][Gripper] Gripper constraint has been removed!")

    # ----------------------------------------------------------------
    # Functions for interact
    # ----------------------------------------------------------------

    def sim_interactive_control_eef(self, duration=20):
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Interact start!")
        if "x" not in self.interact_params: self.interact_params["x"] = p.addUserDebugParameter("x", -0.224, 0.224, 0)
        if "y" not in self.interact_params: self.interact_params["y"] = p.addUserDebugParameter("y", -0.224, 0.224, 0)
        if "z" not in self.interact_params: self.interact_params["z"] = p.addUserDebugParameter("z", 0, 1.0, 0.5)
        if "roll" not in self.interact_params: self.interact_params["roll"] = p.addUserDebugParameter("roll", -math.pi, math.pi, 0)
        if "pitch" not in self.interact_params: self.interact_params["pitch"] = p.addUserDebugParameter("pitch", -math.pi, 2* math.pi, math.pi)
        if "yaw" not in self.interact_params: self.interact_params["yaw"] = p.addUserDebugParameter("yaw", -math.pi, math.pi, 0)
        # if "gripper_open_width" not in self.interact_params: self.interact_params["gripper_open_width"] = p.addUserDebugParameter("gripper_open_width", self.gripper_range[0], self.gripper_range[1], 0)
        # last_params = [0, 0, 0, 0, math.pi, 0]
        
        start_time = time.time()
        while time.time() - start_time < duration:
            x = p.readUserDebugParameter(self.interact_params["x"])
            y = p.readUserDebugParameter(self.interact_params["y"])
            z = p.readUserDebugParameter(self.interact_params["z"])
            roll = p.readUserDebugParameter(self.interact_params["roll"])
            pitch = p.readUserDebugParameter(self.interact_params["pitch"])
            yaw = p.readUserDebugParameter(self.interact_params["yaw"])
            # curr_params = [x, y, z, roll, pitch, yaw]
            # if not all(abs(a - b) < 0.005 for a, b in zip(curr_params, last_params)):
            #     curr_pos = self.sim_get_current_eef_pose().get_position()
            #     interact_pose = Pose([x+curr_pos[0], y+curr_pos[1], z+curr_pos[2]], [roll, pitch, yaw])
            #     # gripper_opening_width = p.readUserDebugParameter(self.interact_params["gripper_open_width"])
            #     self.sim_move_eef_to_goal_pose(interact_pose)
            # last_params = curr_params
            # self.sim_move_gripper(gripper_opening_width)
            pos = (x, y, z)
            orn = p.getQuaternionFromEuler((roll, pitch, yaw))
            joint_poses = p.calculateInverseKinematics(self.arm_id, self.eef_id, pos, orn,
                                                       self.arm_lowerLimit, self.arm_upperLimit, self.arm_jointRange, self.arm_reset_jointValues,
                                                       maxNumIterations=20)
            for i, joint_id in enumerate(self.arm_joints_idx):
                p.setJointMotorControl2(self.arm_id, joint_id, p.POSITION_CONTROL, joint_poses[i],
                                        force=self.arm_jointInfo[joint_id].maxForce, maxVelocity=self.arm_jointInfo[joint_id].maxVelocity)
            self.client.run(120)
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Interact over!")

    # ----------------------------------------------------------------
    # Functions for pick and place
    # ----------------------------------------------------------------

    def pick(self, pick_pose):
        """
        Pick up the specified object without collision.

        Args:
            pick_pose (Pose): pick pose
        """
        pick_position, pick_orientation = (
            pick_pose.get_position(),
            pick_pose.get_orientation(),
        )
        tmp_pose1 = Pose(
            [pick_position[0], pick_position[1], pick_position[2] + 0.06],
            pick_orientation,
        )
        tmp_pose2 = Pose(
            [pick_position[0], pick_position[1], pick_position[2] - 0.03],
            pick_orientation,
        )
        tmp_pose3 = Pose(
            [pick_position[0], pick_position[1], pick_position[2] + 0.5],
            pick_orientation,
        )
        self.sim_move_eef_to_goal_pose(tmp_pose1, 100)
        self.sim_open_gripper()
        self.sim_move_eef_to_goal_pose(tmp_pose2, 100)
        self.sim_close_gripper()
        self.sim_move_eef_to_goal_pose(tmp_pose3, 100)

    def place(self, place_pose):
        """
        Place an object at the specified goal pose without collision.

        Args:
            place_pose (Pose): The pose where the object will be placed.
        """
        place_position, place_orientation = (
            place_pose.get_position(),
            place_pose.get_orientation(),
        )
        tmp_pose1 = Pose(
            [place_position[0], place_position[1], place_position[2] + 0.06],
            place_orientation,
        )
        self.sim_move_eef_to_goal_pose(tmp_pose1, 100)
        self.sim_move_eef_to_goal_pose(place_pose, 100)
        self.sim_open_gripper()

    def pick_place(self, object, goal_pose):
        """
        Perform a pick and place operation.

        Args:
            object (str): The name or ID of the object to be picked up.
            goal_pose (Pose): The pose where the object will be placed.
        """
        self.pick(object)
        self.place(goal_pose)

    # ----------------------------------------------------------------
    # functions for transform
    # ----------------------------------------------------------------

    def align_grasp_pose_to_tcp(self, z_init, target_pose):
        """
        Computes the homogeneous transformation matrix that aligns the z-axis of the target pose to the z-axis of the initial pose.

        Args:
            R_init (np.ndarray): 4x4 homogeneous matrix representing the initial rotation and translation of the end of the robot.
            R_target (np.ndarray): 4x4 homogeneous matrix representing the rotation and translation of the target grasp.

        Returns:
            np.ndarray: 4x4 homogeneous transformation matrix that aligns the z-axis of the target to the z-axis of the initial pose.
        """
        R_target_rot = target_pose.get_orientation("rotation_matrix")[:3, :3]
        z_target = R_target_rot[:, 2]

        v = np.cross(z_target, z_init)
        v_norm = np.linalg.norm(v)

        if v_norm == 0:
            R_align = np.eye(3)
        else:
            v = v / v_norm
            theta = np.arccos(np.dot(z_target, z_init))
            R_align = R.from_rotvec(theta * v).as_matrix()

        R_final_rot = R_align @ R_target_rot
        target_pose = Pose(target_pose.get_position(), R_final_rot)
        return target_pose
