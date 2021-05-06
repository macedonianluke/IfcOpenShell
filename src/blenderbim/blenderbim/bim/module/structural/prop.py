import bpy
from math import radians
from blenderbim.bim.prop import StrProperty, Attribute
from bpy.types import PropertyGroup
from bpy.props import (
    PointerProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    CollectionProperty,
)


def updateAxisAngle(self, context):
    if not self.axis_empty:
        return
    obj = context.active_object
    empty = self.axis_empty
    x_axis = obj.data.vertices[1].co - obj.data.vertices[0].co
    empty.location = obj.data.vertices[0].co
    empty.rotation_mode = "QUATERNION"
    empty.rotation_quaternion = x_axis.to_track_quat("X", "Z")
    empty.rotation_mode = "XYZ"
    empty.rotation_euler[0] = radians(self.axis_angle)

def updateConnectionCS(self, context):
    if not self.ccs_empty:
        return
    obj = context.active_object
    empty = self.ccs_empty
    empty.location = obj.data.vertices[0].co
    empty.rotation_mode = "XYZ"
    empty.rotation_euler[0] = radians(self.ccs_x_angle)
    empty.rotation_euler[1] = radians(self.ccs_y_angle)
    empty.rotation_euler[2] = radians(self.ccs_z_angle)


class StructuralAnalysisModel(PropertyGroup):
    name: StringProperty(name="Name")
    ifc_definition_id: IntProperty(name="IFC Definition ID")


class BIMStructuralProperties(PropertyGroup):
    structural_analysis_model_attributes: CollectionProperty(
        name="Structural Analysis Model Attributes", type=Attribute
    )
    is_editing: BoolProperty(name="Is Editing", default=False)
    structural_analysis_models: CollectionProperty(name="Structural Analysis Models", type=StructuralAnalysisModel)
    active_structural_analysis_model_index: IntProperty(name="Active Structural Analysis Model Index")
    active_structural_analysis_model_id: IntProperty(name="Active Structural Analysis Model Id")
    load_case_editing_type: StringProperty(name="Load Case Editing Type")
    load_case_attributes: CollectionProperty(name="Load Case Attributes", type=Attribute)
    active_load_case_id: IntProperty(name="Active Load Case Id")


class BIMObjectStructuralProperties(PropertyGroup):
    boundary_condition_attributes: CollectionProperty(name="Boundary Condition Attributes", type=Attribute)
    active_boundary_condition: IntProperty(name="Active Boundary Condition")
    active_connects_structural_member: IntProperty(name="Active Connects Structural Member")
    relating_structural_member: PointerProperty(name="Relating Structural Member", type=bpy.types.Object)
    is_editing_axis: BoolProperty(name="Is Editing Axis", default=False)
    axis_angle: FloatProperty(name="Axis Angle", update=updateAxisAngle)
    axis_empty: PointerProperty(name="Axis Empty", type=bpy.types.Object)

    # relating_structural_activity: PointerProperty(name="Relating Structural Activity", type=bpy.types.Object)
    is_editing_connection_cs: BoolProperty(name="Is Editing Connection CS", default=False)
    ccs_x_angle: FloatProperty(name="Connection CS X Angle", update=updateConnectionCS)
    ccs_y_angle: FloatProperty(name="Connection CS Y Angle", update=updateConnectionCS)
    ccs_z_angle: FloatProperty(name="Connection CS Z Angle", update=updateConnectionCS)
    ccs_empty: PointerProperty(name="CCS Empty", type=bpy.types.Object)
