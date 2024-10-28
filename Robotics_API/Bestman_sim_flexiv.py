# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
# @FileName       : Bestman_sim_flexiv.py
# @Time           : 2024-08-03 15:08:13
# @Author         : yk
# @Email          : yangkui1127@gmail.com
# @Description:   : flexiv robot
"""

import math
import time

import numpy as np
import pybullet as p
from scipy.spatial.transform import Rotation as R

from .Bestman_sim import Bestman_sim
from .Pose import Pose


class Bestman_sim_flexiv(Bestman_sim):
    """
    A class representing a simulation for the Bestman robot equipped with a flexiv arm.
    """

    def __init__(self, client, visualizer, cfg):
        """
        Initialize the Bestman_sim_flexiv with the given parameters.

        Args:
            client (int): The PyBullet client ID.
            visualizer (bool): Flag indicating whether visualization is enabled.
            cfg (dict): Configuration settings.
        """

        # Init parent class: BestMan_sim
        super().__init__(client, visualizer, cfg)

        # change robot color
        self.visualizer.set_object_color(self.base_id, "light_white")
        
        # gripper range
        self.gripper_range = [0, 0.085]
        
        # create gripper constraints
        self.create_eef_constraints()
        
        # # gripper constraints
        # c = p.createConstraint(self.arm_id, 10, self.arm_id, 11, p.JOINT_POINT2POINT, [0, 0, 0], [0, -0.014, 0.043], [0, -0.034, 0.021])
        # p.chngeConstraint(c, erp=0.1, maxForce=1000)
        
        # c = p.createConstraint(self.arm_id, 12, self.arm_id, 13, p.JOINT_POINT2POINT, [0, 0, 0], [0, -0.014, 0.043], [0, -0.034, 0.021])
        # p.changeConstraint(c, erp=0.1, maxForce=1000)
        
        # p.setJointMotorControl2(self.arm_id, 10, p.VELOCITY_CONTROL, targetVelocity=0, force=0)
        # p.setJointMotorControl2(self.arm_id, 11, p.VELOCITY_CONTROL, targetVelocity=0, force=0)
        # p.setJointMotorControl2(self.arm_id, 12, p.VELOCITY_CONTROL, targetVelocity=0, force=0)
        # p.setJointMotorControl2(self.arm_id, 13, p.VELOCITY_CONTROL, targetVelocity=0, force=0)
        
        
        # c = p.createConstraint(self.arm_id, 8, self.arm_id, 14, p.JOINT_GEAR, [1, 0, 0], [0, 0, 0], [0, 0, 0])
        # p.changeConstraint(c, gearRatio=-1, erp=0.1, maxForce=50)
        
        # # gripper control
        # p.setJointMotorControlMultiDofArray(self.arm_id, [8, 14], p.POSITION_CONTROL, [[q], [q]], forces=[[t], [t]])a

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

    def create_eef_constraints(self):
        """
        Create constraints for the gripper to control the gripper state。
        """
        
        # defines the child joints that move synchronously with the parent joint and their movement ratio
        mimic_parent_name = 'finger_joint'
        mimic_children_names = {'right_outer_knuckle_joint': 1,
                                'left_inner_knuckle_joint': 1,
                                'right_inner_knuckle_joint': 1,
                                'left_inner_finger_joint': -1,
                                'right_inner_finger_joint': -1}
        
        # establish gear ratios for the parent and child joints in the gripper
        self.mimic_parent_id = [jointInfo.id for jointInfo in self.arm_jointInfo if jointInfo.name == mimic_parent_name][0]
        self.mimic_child_multiplier = {jointInfo.id: mimic_children_names[jointInfo.name] for jointInfo in self.arm_jointInfo if jointInfo.name in mimic_children_names}
        for joint_id, multiplier in self.mimic_child_multiplier.items():
            c = p.createConstraint(self.arm_id, self.mimic_parent_id,
                                   self.arm_id, joint_id,
                                   jointType=p.JOINT_GEAR,
                                   jointAxis=[0, 1, 0],
                                   parentFramePosition=[0, 0, 0],
                                   childFramePosition=[0, 0, 0])
            p.changeConstraint(c, gearRatio=-multiplier, maxForce=100, erp=1)  # Note: the mysterious `erp` is of EXTREME importance
    
    def sim_open_gripper(self):
        """open gripper"""
        self.sim_move_gripper(self.gripper_range[1])
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Gripper open!")

    def sim_close_gripper(self):
        """close gripper"""
        self.sim_move_gripper(self.gripper_range[0])
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Gripper close!")
    
    def sim_move_gripper(self, open_width):
        # open_length = np.clip(open_length, *self.gripper_range)
        open_angle = 0.715 - math.asin((open_width - 0.010) / 0.1143)  # angle calculation
        # Control the mimic gripper joint(s)
        p.setJointMotorControl2(self.arm_id, self.mimic_parent_id, p.POSITION_CONTROL, targetPosition=open_angle,
                                force=self.arm_jointInfo[self.mimic_parent_id].maxForce, maxVelocity=self.arm_jointInfo[self.mimic_parent_id].maxVelocity)
        self.client.run(30)
        
    def sim_interactive_set_gripper(self, duration=20):
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Interact start!")
        if self.gripper_control is None:
            gripper_control = p.addUserDebugParameter(
                "gripper", self.gripper_range[0], self.gripper_range[1], 0
            )
        start_time = time.time()
        while time.time() - start_time < duration:
            target_gripper_width = p.readUserDebugParameter(gripper_control)
            self.sim_move_gripper(target_gripper_width)
        print("[BestMan_Sim][Gripper] \033[34mInfo\033[0m: Interact over!")
        
    
        