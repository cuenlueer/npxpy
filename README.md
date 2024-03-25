# nanoAPI
## Prerequisites
- Python 3
- Python-packages: `toml, uuid, json, datetime, os` 
## Introduction
The here provided custom API *nanoAPI* for the **NanoScribe QX** attempts to emulate the logic of its out-of-the-box
GUI-software *NanoPrintX* by means of plain-text-manipulation only. Three classes are implemented to accomplish this:

1. Presets: `nanoAPI.Preset()`
2. Resources: `nanoAPI.Resource()`
3. Nodes: `nanoAPI.Node()`

These three classes are the backbone of *nanoAPI* since they make up the main building blocks of how the .nano-files are structured.
In order to go through the functionalities of each class it is most reasonable to go through one example of how a .nano-file is created.
However, as of yet there is no way of telling what parameters are mandatory for the .nano-files to work. Therefore, in the following example
the parameters which do appear but seem to be redundant are going to be commented with `#here-to-stay value` or `#hts value`. The user is
therefore hereby encouraged to just experiment with leaving out some of those parameters and check if the project files still work.

## Example Project
