# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:49:39 2024

@author: CU
"""

project = npxpy.Project(objective, resin, substrate)

coarse_aligner = npxpy.Coarse_Aligner(name, residual_threshold).make_anchors(position_label, position)
coarse_aligner.add_anchor(label, position)


project.add_child(coarse_aligner)

scene = npxpy.Scene(name, print_dir).create_at(Position)


















project.nano('name_of_file') #Soll resources suchen und error ausgeben wenn nicht gefunden