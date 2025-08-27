# CHANGELOG


## v0.2.0 (2025-08-27)

### Bug Fixes

- Deepcopy_node alignment_anchors issue
  ([`25c53c0`](https://github.com/cuenlueer/npxpy/commit/25c53c00736928c01beba48da2a09e49d0049df6))

### Features

- Implement auto loading for presets/resources
  ([`fc6009a`](https://github.com/cuenlueer/npxpy/commit/fc6009acc37e54c7cc757e4430c93cc8a008619c))

- Implemented auto loading flags for images/meshes/presets. - Fixed possible multiloading of same
  instances for meshes/presets during export. - Introduced 10x objective as possible parameter

- Implement method .get_scenes()
  ([`38e8ae4`](https://github.com/cuenlueer/npxpy/commit/38e8ae45c738f3610f26aa3b847df89e0e8a5e4e))

- Implemented new method that is supposed to supersede method .marker_aligned_printing(). - Enhanced
  method .gds_printing() by introducing option to tile for each polygon instead of the enclosing
  bbox.


## v0.1.3 (2025-03-28)

### Bug Fixes

- Hotfix missing positional argument: 'mesh'
  ([`50e0dfa`](https://github.com/cuenlueer/npxpy/commit/50e0dfa8d669613ae1f341828f5b0b92c28fd95d))


## v0.1.2 (2025-03-28)

### Bug Fixes

- Attributes assigned but never passed to_dict()
  ([`f20d514`](https://github.com/cuenlueer/npxpy/commit/f20d51441dfaf6da68221891fd69c596ce556123))

- Enforce passing of Preset and Mesh args
  ([`7680c97`](https://github.com/cuenlueer/npxpy/commit/7680c97ec33787d85ec794d73d80ce7c206a20e8))

Keeping Preset/Mesh for structures optional may cause issues with the TOML-parser during export if
  not passed.

- Resize pyvista text mesh for potential linebreaks
  ([`a8e9bf5`](https://github.com/cuenlueer/npxpy/commit/a8e9bf56f8d6a038a751cab36d7faba5be75d3fe))

- Return self when appending nodes
  ([`647cca4`](https://github.com/cuenlueer/npxpy/commit/647cca4af3fe583d81f51995bb9f790e2440fb82))

### Documentation

- Add introductory example to Examples tab
  ([`28952ba`](https://github.com/cuenlueer/npxpy/commit/28952bac30ae4804c7b8e9ab1704ac294214f95a))

- Change "Tutorials" section to "User Guide"
  ([`de84b3e`](https://github.com/cuenlueer/npxpy/commit/de84b3e7cf4623f407f342909125bcdd28fbd595))

- Create download for full example
  ([`1fd0ecf`](https://github.com/cuenlueer/npxpy/commit/1fd0ecf6e298ab3a4231d792deb549848980bb2b))

docs: zip example

- Reorganize example section
  ([`d3329c5`](https://github.com/cuenlueer/npxpy/commit/d3329c547b9002480e9845f13c89b40ea4720eee))


## v0.1.1 (2025-03-17)

### Bug Fixes

- Enhance data validation for position/rotation
  ([`8a580ff`](https://github.com/cuenlueer/npxpy/commit/8a580ff09a26a47af8a23a7fb1ca2ccbc4c31fc5))

- Implement a gatekeeper node class for better maintainability of nodes with position/rotation
  attributes.

- Enable input of arbitrary iterable types and force entry datatypes to be float.

### Documentation

- Add metadata references
  ([`820c192`](https://github.com/cuenlueer/npxpy/commit/820c192404da1a148a14416d495d245882b4657d))

- Deploy documentation
  ([`3213278`](https://github.com/cuenlueer/npxpy/commit/3213278a48e4a64d9b3c6700b86628f241217e22))


## v0.1.0 (2025-03-17)

### Bug Fixes

- Release on PyPI
  ([`ad2c923`](https://github.com/cuenlueer/npxpy/commit/ad2c9237f3e0cd8666d1980ad3049e145c1b4915))

### Documentation

- Prepare docs for deployment
  ([`baae993`](https://github.com/cuenlueer/npxpy/commit/baae9938e81c320d4ff53287000c34918e1c4f13))


## v0.0.0 (2025-03-15)

### Bug Fixes

- Add parent_node missing in deepcopy_node
  ([`f992fd8`](https://github.com/cuenlueer/npxpy/commit/f992fd8d1aacba91c0c507331b1037d14f089bde))

perf: implement recursive deepcopy_node

chores: rename parents_nodes to parent_node

- Add type check if input translation is list
  ([`c2e10dd`](https://github.com/cuenlueer/npxpy/commit/c2e10dd3b770bb1c75ded64631b387ac937cf7ca))

- Auto_load() for structure
  ([`1c13a69`](https://github.com/cuenlueer/npxpy/commit/1c13a695b0259e4eef61ca68c5fedd54a32be12d))

- Case where len(position)=1
  ([`9571430`](https://github.com/cuenlueer/npxpy/commit/957143093d23f6bc25871ea279ee2f6432562746))

- Check for scene and not calling node (ronin scene check)
  ([`d274b6b`](https://github.com/cuenlueer/npxpy/commit/d274b6b7f7ec77c6689b4a66925e8725afa543fc))

- Empty mesh plotting issues
  ([`9a5bfc5`](https://github.com/cuenlueer/npxpy/commit/9a5bfc57060d35c286b9ed355494516209bde2f8))

Reason as to why this issue comes up is not apparent. Setting global theme accordingly seems to fix
  the issue though.

- Error in previous optimization
  ([`526c559`](https://github.com/cuenlueer/npxpy/commit/526c559e030972003c63575a8b4a954b432acf01))

- File_path instead of path variable in resources
  ([`a592250`](https://github.com/cuenlueer/npxpy/commit/a59225009dfd8ebe9043dbdd6168cefbd5a095ee))

- Implement clean getter for node_type
  ([`961b668`](https://github.com/cuenlueer/npxpy/commit/961b668a17325a91e2ddd72d35ae957107bc8866))

- Implement errorhandling
  ([`3539a54`](https://github.com/cuenlueer/npxpy/commit/3539a54924b43d085fd52982d8def48c6bba8e15))

chores: add typing/docstrings/refactoring

- Implement method _auto_center in Mesh
  ([`56a6eb2`](https://github.com/cuenlueer/npxpy/commit/56a6eb2616d6139038b44a6f124904c65dee3c61))

- Implement new argument ordering
  ([`743b8ca`](https://github.com/cuenlueer/npxpy/commit/743b8caaace7ccae5b6e7ea04042136f60f22e35))

- Logo issues when calling viewport
  ([`8e1aea2`](https://github.com/cuenlueer/npxpy/commit/8e1aea256cb830703acc2ffda2f8456ff2d2a8f6))

fix: remove/adjust versioning/redundant package declarations

- Marker aligner takes three positions as it should.
  ([`b4190d1`](https://github.com/cuenlueer/npxpy/commit/b4190d1f0362bc0e41655eba05fc01de55a25064))

- Optimize routines
  ([`f989829`](https://github.com/cuenlueer/npxpy/commit/f989829331c8bb7bd575a37df9bd37fc2efe6d94))

- Optimized generation of all_ancestors/all_descendants - Omit self.geometry in .to_dict()

- Order of arguments for and in methods
  ([`d24c509`](https://github.com/cuenlueer/npxpy/commit/d24c5092c06970cb8c161323ddf052e4dd260433))

- Position_at rotation reset only if is not None
  ([`fe46e67`](https://github.com/cuenlueer/npxpy/commit/fe46e673844651cb92c75c17feae3504d1a0d920))

- Pull return out of loop in add_child method
  ([`ea58ebd`](https://github.com/cuenlueer/npxpy/commit/ea58ebda6d7718fc28e98774b9308aa7c45da044))

- Rename resin to resist in project_info dict
  ([`de62388`](https://github.com/cuenlueer/npxpy/commit/de62388bea08e9470ba769679986cae8d91134d4))

- Set default position/rotation for structure.postion_at()
  ([`28a1834`](https://github.com/cuenlueer/npxpy/commit/28a1834cab6f40b3096182b04c8ce274229139a1))

- Typo
  ([`77196e1`](https://github.com/cuenlueer/npxpy/commit/77196e1d7d9c78d4bea8753d43bdb6591308708e))

- Unpack in grab_node()
  ([`ef972b2`](https://github.com/cuenlueer/npxpy/commit/ef972b266638981318834eeb6997bdfe6fb0e268))

- Viewport cases for block render
  ([`8dff02d`](https://github.com/cuenlueer/npxpy/commit/8dff02d83263661f9f5e1d2d6657811e0d07515d))

feat: enhance append_node by applying as *args

### Chores

- Exchange toml with pytomlpp
  ([`d739de6`](https://github.com/cuenlueer/npxpy/commit/d739de6b2e879a5f5cd632a7dc8f549ac4608c4d))

### Documentation

- Add example for stl sweep
  ([`2fe6baf`](https://github.com/cuenlueer/npxpy/commit/2fe6baf015ecfe50f9e6264af73a726a33e4613c))

- Add examples (menger sponge and STL sweep)
  ([`ed7430d`](https://github.com/cuenlueer/npxpy/commit/ed7430dabaa91cfc0558ac907715ad9e0227d996))

- Adjusting and expanding on examples
  ([`3f9f3ac`](https://github.com/cuenlueer/npxpy/commit/3f9f3ac5de73e9975d1dbd2d9f8f2a4cb69547ca))

- Adjusting/adding resources
  ([`5296a20`](https://github.com/cuenlueer/npxpy/commit/5296a20e36cf29cf788e49ed1690c94c34e70df8))

- Fix installation instructions
  ([`ec96eb8`](https://github.com/cuenlueer/npxpy/commit/ec96eb8e0aa7b4186726c755564a1cfb68eb50c4))

- Fix typo
  ([`caec77d`](https://github.com/cuenlueer/npxpy/commit/caec77db56025dd5b09103376fea24425729474e))

- Prepare for release
  ([`e2471d4`](https://github.com/cuenlueer/npxpy/commit/e2471d423f287283d460319331d26ffe743a4326))

### Features

- Add (optional) submodule
  ([`8c10b4e`](https://github.com/cuenlueer/npxpy/commit/8c10b4e4f97b49e9d7fe6a751460c1320fddacd6))

- Display color in viewport
  ([`69ac6c3`](https://github.com/cuenlueer/npxpy/commit/69ac6c3b263316b2d7cdc177b6d686b94b3de04e))

- Handle resources/presets now as *args
  ([`ee1ebdd`](https://github.com/cuenlueer/npxpy/commit/ee1ebdd6fb9d24169b42620d302f02a5f6cf4016))

- Implement default labels
  ([`3fceb1a`](https://github.com/cuenlueer/npxpy/commit/3fceb1a3710f13661e862bdab1ac768c5b73b771))

more flexible input for interface anchors by list slicing/type handling

- Implement new method auto_load
  ([`1260c25`](https://github.com/cuenlueer/npxpy/commit/1260c255b586ea9b6503c46afb22e0097c2af63c))

- Implement project.viewport()
  ([`8fb8235`](https://github.com/cuenlueer/npxpy/commit/8fb8235488fdc267c38deb8adba69892c4f5fd91))

Current implementation is a rough prototype still missing some the visualization of some objects.
  Refactoring necessary. chore: Exchange toml for pytomlpp in preset.py

- Migrate viewport from Project to Node
  ([`4127f7b`](https://github.com/cuenlueer/npxpy/commit/4127f7b0c9914e9a4bc713d7fe8f5c416e42961e))

- Add labels for markers in viewport - Add xyz-axes to viewport

- Project-viewport implementation
  ([`fec23e9`](https://github.com/cuenlueer/npxpy/commit/fec23e9fe973d21ad3968136cdef7f4848b27c24))

### Performance Improvements

- Increase opacity of marker labels
  ([`c2f838f`](https://github.com/cuenlueer/npxpy/commit/c2f838fd7746b50e6fde5f7d110ea2bcb1638721))

- Try to introduce compositions via pv.MultiBlock()
  ([`abc6c86`](https://github.com/cuenlueer/npxpy/commit/abc6c8669a4faad6611c307bcebf516ea98ad3bc))

### Testing

- Add minor changes for viewport testing
  ([`6848119`](https://github.com/cuenlueer/npxpy/commit/6848119581a333ab953febab8070df6b7bef5367))

- Added some readme
  ([`019612b`](https://github.com/cuenlueer/npxpy/commit/019612b04ab1898b41d9a8303accee8d18c8a3f6))

- Refined test cases for multiple nodes.
  ([`c40a398`](https://github.com/cuenlueer/npxpy/commit/c40a398742f513c29571e02879945202088f1dd1))
