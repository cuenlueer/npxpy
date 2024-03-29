# nanoAPI
0.0.0-alpha

## Prerequisites
- Python 3
- Python-packages: `toml, uuid, json, subprocess, time, datetime, os, shutil, hashlib`
- [7-Zip](https://7-zip.org/)

## Introduction
The here provided custom API *nanoAPI* for the **NanoScribe QX** attempts to emulate the logic of its out-of-the-box
GUI-software *NanoPrintX* by means of plain-text-manipulation and open-source-tools only. Just three classes are implemented to accomplish this
in a concise manner:

1. Presets: `nanoAPI.Preset()`
2. Resources: `nanoAPI.Resource()`
3. Nodes: `nanoAPI.Node()`

These three classes are the backbone of *nanoAPI* since they make up the main building blocks of how the .nano-files are structured.
In order to go through the functionalities of each class it is most reasonable to go through one example of how a .nano-file is created.
However, before doing so, a brief outline of the API's scripting logic is crucial since the rather abstract nature of plain-text
implementation of the intuitively clear and accessible GUI will inevitably have a more alien feel to it. Therefore, an illustrative
guide of the API's logic can help understanding the order of implementation before diving into the actual code for the .nano-generation. 

## Schematic Outline
**ATTENTION:** *It is assumed that the reader has already familiarized themselves with the NanoPrintX-GUI's workflow before proceeding with the following doc!*
*No additional introduction will be given for the GUI beforehand.*

Working with the GUI is straightforward and user friendly: You have your three tabs designated as 'Treeview', 'Presets', 'Resources' and the rest is
pretty much straightforward from there. You import your resources, i.e., images (.png)  and meshs (.stl), set your presets and then get started with
structuring your project by inserting your children-nodes to your main project-node and set your node settings on the fly (see Fig. 1).

The way of how *nanoAPI* handles things is quite similiar with the exception being that you can also define your nodes and set the node settings <ins>before<ins> 
you assign them as parents or children (see Fig. 2). Breaking the workflow structure up like this not only gives the user the ability to have a more customized project workflow
but also to keep their code more readable by, as for instance, implementing the node allocation in a seperated code block.
The presets and resources, however, should always be defined from the outset in order to allocate them while setting up marker-aligner-nodes and/or
structure-nodes. Although syntactically inconvenient, there is propably no issue doing it otherwise. However, it is strongly suggested to define them always first for semantic reasons.

After having set up all nodes, one can start allocating them in their respective parent-child-order (see Fig. 3; Once again: It is possible to do this the
other way around here as well but it is probably easier in most situations to keep track of your code by sticking to the described structure here).

The last step is always the same, where all objects are collected according to their classed, preprocessed and wrapped up into the .nano-format (see Fig. 4). 


## Example Project
First, we need to import all neccessary packages to our project.py and define a dictionary that contains some meta data about our project. 

```
import nanoAPI as n
from datetime import datetime
import os

project_info_json = {
                      "author": "Caghan (work)",
                      "objective": "25x",
                      "resist": "IP-n162",
                      "substrate": "FuSi",
                      "creation_date": datetime.now().replace(microsecond=0).isoformat()
                    }


```
text
```
edit_presets = {"writing_speed" : 250000.0,
                "writing_power" : 50.0,
                "slicing_spacing" : 0.8,
                "hatching_spacing" : 0.3,
                "hatching_angle" : 0.0,
                "hatching_angle_increment" : 0.0,
                "hatching_offset" : 0.0,
                "hatching_offset_increment" : 0.0,
                "hatching_back_n_forth" : True,
                "mesh_z_offset" : 0.0}

preset = n.Preset(name = "25x_IP-n162_anchorage_FuSi_clone", **edit_presets)




resource_mesh = n.Resource(resource_type = "mesh_file",
                           name = "structure",
                           path = "5416ba193f0bacf1e37be08d5c249914/combined_file.stl")

resource_image = n.Resource(resource_type = "image_file",
                            name = "markers_1",
                            path = "78eab7abd2cd201630ba30ed5a7ef4fc/markers.png")

```
text
```
#Tree view_________________________________________________________

project = n.Node(node_type='project',
                 name = 'Project 1',
                 objective = project_info_json['objective'],
                 resin = project_info_json['resist'],
                 substrate = project_info_json['substrate'])

#-----------------------------------------------
```
text
```
coarse_aligner1 = n.Node(node_type = 'coarse_alignment',
                        name = "Coarse aligner 1",
                        residual_threshold = 10.0,
                        orthonormalize = True # here-to-stay value
                        ) 
labels = ['anchor 0',
          'anchor 1',
          'anchor 2',
          'anchor 3']

positions = [[-60.0, -528.0, 0.0],
             [-130.0, -528.0, 0.0],
             [-60.0, 20.0, 0.0],
             [-130.0, 20.0, 0.0]]

for label, position in zip(labels,positions):
    coarse_aligner1.add_coarse_anchor(label, position)
    
#-----------------------------------------------
```
test
```
scene1 = n.Node('scene',
                "Scene 1",
                writing_direction_upward = True)
#-----------------------------------------------
group1 = n.Node('group',
                'Group 1')
#-----------------------------------------------
array1 = n.Node('array',
                'Array 1')
#-----------------------------------------------
```
text
```
interface_aligner1 = n.Node(node_type = 'interface_alignment',
                            name = 'Interface aligner 1',
                            action_upon_failure = "abort",
                            #scan_area_res_factors = [1.0,1.0], # here-to-stay value
                            #laser_power = 0.5, #hts value
                            #scan_area_size = [10.0,10.0], #hts value
                            #scan_z_sample_distance = 0.1, #hts value
                            #scan_z_sample_count = 51, #hts value
                            properties = {"signal_type": "fluorescence"},
                            pattern = "Custom",
                            #area_measurement = False, # here-to-stay
                            measure_tilt = True) 

labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3',
          'marker 4',
          'marker 5',
          'marker 6',
          'marker 7']

positions = [[-130.0, -30.0],
             [-130.0, 30.0],
             [-60.0, -30.0],
             [-60.0, 30.0],
             [-130.0, -60.0],
             [-130.0, 60.0],
             [-60.0, -60.0],
             [-60.0, 60.0]]

scan_area_sizes = [[10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0]]

for label, position, scan_area_size in zip(labels,positions,scan_area_sizes):
    interface_aligner1.add_interface_anchor(label, position,scan_area_size)

#-----------------------------------------------
```
text
```
marker_aligner_defualt = {
    "scan_area_res_factors" : [2,2],
    "laser_power" : 0.5,
    "detection_margin" : 5.0,
    "correlation_threshold" : 60.0,
    "residual_threshold" : 0.5,
    "max_outliers" : 0,
    "orthonormalize" : True,
    "z_scan_sample_count" : 1,
    "z_scan_sample_distance" : 0.5,
    "z_scan_optimization_mode" : "correlation",
    "measure_z" : False,
    }

marker_dict = {
    "image": resource_image.id,
    "size": [5.0,5.0]
    }

marker_aligner1 = n.Node(node_type = "marker_alignment",
                         name = "Marker aligner 1",
                         marker = marker_dict,
                         **marker_aligner_defualt)

labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3']

positions = [[-60.0, -20.0, 0.0],
             [-130.0, -20.0, 0.0],
             [-60.0, 20.0, 0.0],
             [-130.0, 20.0, 0.0]]

rotations = [0.0,
             0.0,
             0.0,
             0.0]

for label, position, rotation in zip(labels,positions,rotations):
    marker_aligner1.add_marker_anchor(label, position, rotation)
```
text
```
structure1 = n.Node(node_type = "structure",
                    name = "test",
                    preset = preset.id,
                    slicing_origin_reference = "scene_bottom",
                    slicing_offset = 0.0,
                    priority = 0,
                    expose_individually = False,
                    geometry = {"type" : "mesh",
                                "resource" : resource_mesh.id,
                                "scale" : [1.0,1.0,1.0]})


```
text
```
project.add_child(coarse_aligner1)
coarse_aligner1.add_child(scene1)
scene1.add_child(group1)
group1.add_child(array1)
array1.add_child(interface_aligner1)
interface_aligner1.add_child(marker_aligner1)
marker_aligner1.add_child(structure1)

```
text
```

n.save_to_toml([preset],
                    [resource_mesh,
                    resource_image],
                        [project,
                        coarse_aligner1,
                        scene1, group1,
                        array1,
                        interface_aligner1,
                        marker_aligner1,
                        structure1])

n.project_info(project_info_json)

n.nano_file_gen('project_example')


```


## Setup
- Make sure you have all neccessary Python packages installed mentioned above.
- Install 7-Zip as provided by their official website (Linux-users might already have it by default).
- Windows only: Add the 7-Zip-directory in your environment variables settings to PATH.
- Download nanoAPI.py from the repository and make sure your project.py-files can import it.

## Misc
*This section contains things like remarks or pro tips, which might be useful to know but not neccessarily mandatory for understanding how to use nanoAPI.*
-pandas
-validate via nanoprintx and save if u want to feel safe
-However, as of yet there is no way of telling what parameters are mandatory for the .nano-files to work. Therefore, in the following example
the parameters which do appear but seem to be redundant are going to be commented with `#here-to-stay value` or `#hts value`. The user is
therefore hereby encouraged to just experiment with leaving out some of those parameters and check if the project files still work.
