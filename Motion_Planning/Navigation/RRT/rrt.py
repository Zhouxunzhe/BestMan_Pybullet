# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
# @FileName       : rrt.py
# @Time           : 2024-08-03 15:07:17
# @Author         : yk
# @Email          : yangkui1127@gmail.com
# @Description:   : RTT navigation algorithm
"""

import math
import random
from rtree import index
import matplotlib.pyplot as plt
# from ..utils import AreaBounds, plot_rectangle
from Motion_Planning.Navigation.utils import *  # test in this script
from RoboticsToolBox import Pose


class RRTPlanner:
    """Class for RRT planning"""

    class Node:
        """RRT Node"""

        def __init__(self, x, y):
            """
            Initializes the RRT node.

            Args:
                x (float): X-coordinate of the node.
                y (float): Y-coordinate of the node.
            """
            self.x = x
            self.y = y
            self.path_x = []
            self.path_y = []
            self.parent = None

    def __init__(self,
                 robot_size,
                 obstacles_bounds,
                 
                 expand_dis=0.2,
                 path_resolution=0.05,
                 goal_sample_rate=5,
                 max_iter=500,
                 enable_plot=True
        ):
        """
        Initializes the RRT planner.

        Args:
            robot_size (float): The size of the robot.
            obstacles_bounds (list): List of obstacle boundaries.
            expand_dis (float, optional): The distance to expand the tree. Defaults to 0.2.
            path_resolution (float, optional): The resolution of the path. Defaults to 0.05.
            goal_sample_rate (int, optional): The goal sampling rate. Defaults to 5.
            max_iter (int, optional): The maximum number of iterations. Defaults to 500.
            enable_plot (bool, optional): Flag to enable or disable plotting. Defaults to True.
        """
        self.obstacles_bounds = obstacles_bounds
        self.idx = index.Index()
        for id, obstacle_bounds in enumerate(self.obstacles_bounds):
            self.idx.insert(id, obstacle_bounds)
        self.robot_radius = robot_size / 2
        self.play_area = None
        self.expand_dis = expand_dis
        self.path_resolution = path_resolution
        self.goal_sample_rate = goal_sample_rate
        self.max_iter = max_iter
        self.node_list = []
        self.enable_plot = enable_plot

    def plan(self, start_pose, goal_pose):
        """
        RRT path planning.

        Args:
            start_pose (Pose): The starting pose of the robot.
            goal_pose (Pose): The goal pose of the robot.

        Returns:
            list: The planned path as a list of points.
        """

        # only care about x, y
        start_position = start_pose.position[0:2]
        goal_position = goal_pose.position[0:2]

        self.area = AreaBounds(start_position, goal_position, self.obstacles_bounds)
        
        self.start = self.Node(start_position[0], start_position[1])
        self.goal = self.Node(goal_position[0], goal_position[1])
        
        self.node_list = [self.start]
        self.path = None
        for i in range(self.max_iter):
            rnd_node = self.get_random_node()
            nearest_ind = self.get_nearest_node_index(self.node_list, rnd_node)
            nearest_node = self.node_list[nearest_ind]

            new_node = self.steer(nearest_node, rnd_node, self.expand_dis)

            if self.check_if_outside_play_area(new_node, self.play_area) and \
               self.check_collision(
                   new_node):
                self.node_list.append(new_node)

            if self.calc_dist_to_goal(self.node_list[-1].x,
                                      self.node_list[-1].y) <= self.expand_dis:
                final_node = self.steer(self.node_list[-1], self.goal,
                                        self.expand_dis)
                if self.check_collision(
                        final_node):
                    self.path = self.generate_final_course(len(self.node_list) - 1)
                    break
                
        if self.path is None:
            print("[RRT Planner] \033[31merror\033[0m: Cannot find path")
        else:
            print("[RRT Planner] \033[34mInfo\033[0m: found path!")

            # Draw final path
            if self.enable_plot:
                self.visual()

        self.path.reverse()
        return self.path  # cannot find path


    def visual(self):
        """Visualization of routes generated by RTT navigation algorithm."""
        
        # clear current figure
        plt.clf()

        for (x_min, y_min, x_max, y_max) in self.obstacles_bounds:
            plot_rectangle(x_min, y_min, x_max, y_max)
        
        plt.plot(self.start.x, self.start.y, "og")
        plt.plot(self.goal.x, self.goal.y, "xr")
        
        plt.plot([x for (x, _) in self.path], [y for (_, y) in self.path], '-r')
        
        plt.axis([self.area.x_min, self.area.x_max, self.area.y_min, self.area.y_max])
        plt.axis("equal")
        # plt.grid(True)
        plt.title("Navigation Visualization")
        plt.pause(0.01)
        plt.show()
        
        
    def steer(self, from_node, to_node, extend_length=float("inf")):
        """
        Steers from one node towards another node.

        Args:
            from_node (Node): The starting node.
            to_node (Node): The target node.
            extend_length (float, optional): The distance to extend towards the target node. Defaults to infinity.

        Returns:
            Node: The new node after steering.
        """
        new_node = self.Node(from_node.x, from_node.y)
        d, theta = self.calc_distance_and_angle(new_node, to_node)

        new_node.path_x = [new_node.x]
        new_node.path_y = [new_node.y]

        if extend_length > d:
            extend_length = d

        n_expand = math.floor(extend_length / self.path_resolution)

        for _ in range(n_expand):
            new_node.x += self.path_resolution * math.cos(theta)
            new_node.y += self.path_resolution * math.sin(theta)
            new_node.path_x.append(new_node.x)
            new_node.path_y.append(new_node.y)

        d, _ = self.calc_distance_and_angle(new_node, to_node)
        if d <= self.path_resolution:
            new_node.path_x.append(to_node.x)
            new_node.path_y.append(to_node.y)
            new_node.x = to_node.x
            new_node.y = to_node.y

        new_node.parent = from_node

        return new_node

    def generate_final_course(self, goal_ind):
        """
        Generates the final course from start to goal.

        Args:
            goal_ind (int): The index of the goal node.

        Returns:
            list: The final path as a list of points.
        """
        path = [[self.goal.x, self.goal.y]]
        node = self.node_list[goal_ind]
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([node.x, node.y])

        return path

    def calc_dist_to_goal(self, x, y):
        """
        Calculates the distance to the goal.

        Args:
            x (float): The x-coordinate.
            y (float): The y-coordinate.

        Returns:
            float: The distance to the goal.
        """
        dx = x - self.goal.x
        dy = y - self.goal.y
        return math.hypot(dx, dy)

    def get_random_node(self):
        """
        Gets a random node.

        Returns:
            Node: The random node.
        """
        if random.randint(0, 100) > self.goal_sample_rate:
            rnd = self.Node(
                random.uniform(self.area.x_min, self.area.x_max),
                random.uniform(self.area.y_min, self.area.y_max))
        else:  # goal point sampling
            rnd = self.Node(self.goal.x, self.goal.y)
        return rnd
    
    @staticmethod
    def get_nearest_node_index(node_list, rnd_node):
        """
        Gets the index of the nearest node.

        Args:
            node_list (list): The list of nodes.
            rnd_node (Node): The random node.

        Returns:
            int: The index of the nearest node.
        """
        dlist = [(node.x - rnd_node.x)**2 + (node.y - rnd_node.y)**2
                 for node in node_list]
        minind = dlist.index(min(dlist))

        return minind

    @staticmethod
    def check_if_outside_play_area(node, play_area):
        """
        Checks if a node is outside the play area.

        Args:
            node (Node): The node to check.
            play_area (AreaBounds): The play area.

        Returns:
            bool: True if the node is inside the play area, False otherwise.
        """
        if play_area is None:
            return True  # no play_area was defined, every pos should be ok

        if node.x < play_area.xmin or node.x > play_area.xmax or \
           node.y < play_area.ymin or node.y > play_area.ymax:
            return False  # outside - bad
        else:
            return True  # inside - ok


    def check_collision(self, node):
        """
        Checks if a node is in collision.

        Args:
            node (Node): The node to check.

        Returns:
            bool: True if the node is not in collision, False otherwise.
        """
        if node is None:
            return False
        
        for x, y in zip(node.path_x, node.path_y):
            query_area = [x-self.robot_radius, y-self.robot_radius, x+self.robot_radius, y+self.robot_radius]
            intersected_ids = list(self.idx.intersection(query_area))
            if len(intersected_ids) != 0:
                return False

        return True  # safe

    @staticmethod
    def calc_distance_and_angle(from_node, to_node):
        """
        Calculates the distance and angle between two nodes.

        Args:
            from_node (Node): The starting node.
            to_node (Node): The target node.

        Returns:
            tuple: The distance and angle between the nodes.
        """
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        d = math.hypot(dx, dy)
        theta = math.atan2(dy, dx)
        return d, theta


def main():
    
    print("start " + __file__)

    obstacles_bounds = [[4,4,6,6],[1,4,5,8],[1,6,5,10],[1,8,5,12],[5,3,9,7],[7,3,11,7],[7,9,9,11],[7,9,9,11]]
    robot_size = 1.2
    
    # Set Initial parameters
    rrt = RRTPlanner(
        robot_size=robot_size,
        obstacles_bounds = obstacles_bounds,
        expand_dis = 3,
        enable_plot=True
    )
    
    # route plan
    start_pose = Pose([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    goal_pose = Pose([6.0, 10.0, 0.0], [0.0, 0.0, 0.0])
    path = rrt.plan(start_pose, goal_pose)
    print('start:', start_pose.position[0:2])
    print('goal:', goal_pose.position[0:2])
    print('path:', path)




if __name__ == '__main__':
    main()
