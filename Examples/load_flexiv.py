# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
# @FileName       : load_panda.py
# @Time           : 2024-08-03 15:04:37
# @Author         : yk
# @Email          : yangkui1127@gmail.com
# @Description:   : A example load panda robot
"""


import os

from Config import load_config
from Env.Client import Client
from Robotics_API import Bestman_sim_flexiv_robotiq_2f85
from Visualization.Visualizer import Visualizer


def main(filename):

    # load config
    config_path = "Config/load_flexiv.yaml"
    cfg = load_config(config_path)
    print(cfg)

    # Init client and visualizer
    client = Client(cfg.Client)
    visualizer = Visualizer(client, cfg.Visualizer)

    # Start record
    visualizer.start_record(filename)

    # Init robot
    flexiv = Bestman_sim_flexiv_robotiq_2f85(client, visualizer, cfg)

    # Interact with arm
    # flexiv.sim_interactive_control_arm(100)

    # interct with eef
    flexiv.sim_interactive_control_eef(100)

    # client.wait(10)

    # visualizer.capture_screen("flexiv")

    # # End record
    # visualizer.end_record()

    # disconnect pybullet
    client.wait(10)
    client.disconnect()


if __name__ == "__main__":

    # set work dir to Examples
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # get current file name
    file_name = os.path.splitext(os.path.basename(__file__))[0]

    main(file_name)
