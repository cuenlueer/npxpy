import npxpy

#  Initialize the presets and resources that you want to use in this project.
preset_from_file = npxpy.Preset.load_single(file_path = 'preset_from_file.toml')

edit_presets = {"writing_speed" : 220000.0,
                "writing_power" : 50.0,
                "slicing_spacing" : 0.8,
                "hatching_spacing" : 0.3,
                "hatching_angle" : 0.0,
                "hatching_angle_increment" : 0.0,
                "hatching_offset" : 0.0,
                "hatching_offset_increment" : 0.0,
                "hatching_back_n_forth" : True,
                "mesh_z_offset" : 0.0}

preset_from_args = npxpy.Preset(name = 'preset_from_args', **edit_presets)

stl_mesh = npxpy.Mesh(path = './example_mesh.stl', name = 'stl_structure_0')
marker = npxpy.Image(path = './example_marker.png', name = 'marker_image')

#  Initialize project and load your presets and resources.
project = npxpy.Project(objective = '25x', resin = 'IP-n162', substrate = 'FuSi')
project.load_presets([preset_from_file, preset_from_args])
project.load_resources([stl_mesh, marker])

#  Prepare the nodes of your project as you would in nanoPrintX-Treeview.
#  Starting with the coarse aligner.
coarse_aligner = npxpy.CoarseAligner(residual_threshold = 8)

ca_labels = ['anchor 0',
          'anchor 1',
          'anchor 2',
          'anchor 3']
ca_positions = [[200.0, 200.0, 0.0],
             [200.0, -200.0, 0.0],
             [-200.0, -200.0, 0.0],
             [-200.0, 200.0, 0.0]]

coarse_aligner.set_coarse_anchors_at(ca_labels, ca_positions)

#  Initializing printing scene
scene_0 = npxpy.Scene(name = 'scene_0', writing_direction_upward=True)

#  Interface alignment
interface_aligner = npxpy.InterfaceAligner(name = 'Interface Aligner')

ia_labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3',
          'marker 4',
          'marker 5',
          'marker 6',
          'marker 7']

ia_positions = [[-130.0, -30.0],
             [-130.0, 30.0],
             [-60.0, -30.0],
             [-60.0, 30.0],
             [-130.0, -60.0],
             [-130.0, 60.0],
             [-60.0, -60.0],
             [-60.0, 60.0]]

interface_aligner.set_interface_anchors_at(ia_labels, ia_positions)

#  Marker alignment
marker_aligner = npxpy.MarkerAligner(name = 'Marker Aligner', image = marker, marker_size=[10,10])

#  Initialize structure with desired preset and mesh defined above.
structure_0 = npxpy.Structure(name = 'structure_0', preset = preset_from_file, mesh = stl_mesh)

#  Arrange hierarchy of all nodes as desired either with .add_child()...
coarse_aligner.add_child(scene_0)
scene_0.add_child(interface_aligner)

#  ...or more conveniently by using .append_node() to append directly to the lowest node.
scene_0.append_node(marker_aligner)
#
scene_0.append_node(structure_0)

#  Eventually, add all highest-order nodes of interest (here only coarse_aligner) to project.
project.add_child(coarse_aligner)

#  After allocating your nodes, you can copy, manipulate and add additional instances as you like.
scene_1 = scene_0.deepcopy_node(copy_children = True)
scene_1.name = 'scene_1'
scene_1.position = [254, 300, 0]

#  You can access descendants/ancestors as you go via semantically ordered lists.
structure_1 = scene_1.all_descendants[-1]
structure_1.preset = preset_from_args
structure_1.name = 'structure_1'

coarse_aligner.add_child(scene_1)

#  Export your project to a .nano-file.
project.nano(project_name = 'my_project')