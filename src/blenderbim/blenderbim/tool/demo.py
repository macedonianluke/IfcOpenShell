# BlenderBIM Add-on - OpenBIM Blender Add-on
# Copyright (C) 2022 Dion Moult <dion@thinkmoult.com>
#
# This file is part of BlenderBIM Add-on.
#
# BlenderBIM Add-on is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BlenderBIM Add-on is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BlenderBIM Add-on.  If not, see <http://www.gnu.org/licenses/>.

# ############################################################################ #

# Hey there! Welcome to the BlenderBIM Add-on code. Please feel free to reach
# out if you have any questions or need further guidance. Happy hacking!

# ############################################################################ #

# Every module has a tool file which implements all the functions that the core
# needs. Whereas the core is simply high level code, the tool file has the
# concrete implementations, dealing with exactly how things interact with
# Blender's property systems, IFC's data structures, the filesystem, geometry
# processing, and more.

import bpy
import bmesh
import struct
import hashlib
import logging
import numpy as np
import ifcopenshell
import blenderbim.core.tool
import blenderbim.core.style
import blenderbim.core.spatial
import blenderbim.tool as tool
import blenderbim.bim.import_ifc
from math import radians, pi
from mathutils import Vector, Matrix
from blenderbim.bim.ifc import IfcStore
import ifcopenshell.api
import ifcopenshell.util.unit


# There is always one class in each tool file, which implements the interface
# defined by `core/tool.py`.
class Demo(blenderbim.core.tool.Demo):
    @classmethod
    def clear_name_field(cls):
        # In this concrete implementation, we see that "clear name field"
        # actually translates to "set this Blender string property to empty
        # string". In this case, it's pretty simple - but even simple scenarios
        # like these are important to implement in the tool, as it makes the
        # pseudocode easier to read in the core, and makes it easier to test
        # implementations separately from control flow. It also makes it easy to
        # refactor and share functions, where every tool function is captured by
        # a function name that describes its intention.
        bpy.context.scene.BIMDemoProperties.name = ""

    @classmethod
    def get_project(cls):
        return tool.Ifc.get().by_type("IfcProject")[0]

    @classmethod
    def hide_user_hints(cls):
        bpy.context.scene.BIMDemoProperties.show_hints = False

    @classmethod
    def set_message(cls, message):
        bpy.context.scene.BIMDemoProperties.message = message

    @classmethod
    def show_user_hints(cls):
        bpy.context.scene.BIMDemoProperties.show_hints = True
        
    
    

    
    def get_assembly(cls, assembly_name):
        
        model = IfcStore.get_file()
        
        #check if assembly by name already exists
        elements = model.by_type('IfcElementAssembly')
        
        for element in elements:
            if element.Name == assembly_name:
                print("Assembly name already exists")
                return element                
            else:
                pass
            
    @classmethod       
    def create_assembly(cls):

            context = IfcStore.get_file()
            
            print(context)
            
            assembly_name = bpy.context.scene.BIMDemoProperties.assembly_name
            
            storey = context.by_type("IfcBuildingStorey")[0]
            
            assembly = cls.get_assembly(context,assembly_name)
            
            if  assembly is None:           
            
            
                #create wall assemlby
                assembly = ifcopenshell.api.run("root.create_entity",context, ifc_class = "IfcElementAssembly")

                #change name of assembly
                assembly.Name = assembly_name
                
                #assign container
                ifcopenshell.api.run("spatial.assign_container", context, relating_structure = storey, product = assembly)           
                
                print("Assembly created")
                
            else:   
                print("assembly with that name already exists")             
                return None 