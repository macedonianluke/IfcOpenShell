import bpy
import json
import math
import ifcopenshell
import ifcopenshell.util.attribute
from mathutils import geometry
from mathutils import Vector
from blenderbim.bim.ifc import IfcStore


def import_attributes(ifc_class, props, data, callback=None):
    for attribute in IfcStore.get_schema().declaration_by_name(ifc_class).all_attributes():
        data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
        if data_type == "entity":
            continue
        new = props.add()
        new.name = attribute.name()
        new.is_null = data[attribute.name()] is None
        new.is_optional = attribute.optional()
        new.data_type = data_type if isinstance(data_type, str) else ""
        is_handled_by_callback = callback(attribute.name(), new, data) if callback else False
        if is_handled_by_callback:
            pass  # Our job is done
        elif is_handled_by_callback is False:
            props.remove(len(props) - 1)
        elif data_type == "string":
            new.string_value = "" if new.is_null else data[attribute.name()]
        elif data_type == "boolean":
            new.bool_value = False if new.is_null else data[attribute.name()]
        elif data_type == "integer":
            new.int_value = 0 if new.is_null else data[attribute.name()]
        elif data_type == "float":
            new.float_value = 0.0 if new.is_null else data[attribute.name()]
        elif data_type == "enum":
            new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
            if data[attribute.name()]:
                new.enum_value = data[attribute.name()]


def export_attributes(props, callback=None):
    attributes = {}
    for attribute in props:
        is_handled_by_callback = callback(attributes, attribute) if callback else False
        if attribute.is_null:
            attributes[attribute.name] = None
        elif is_handled_by_callback:
            pass  # Our job is done
        elif attribute.data_type == "string":
            attributes[attribute.name] = attribute.string_value
        elif attribute.data_type == "boolean":
            attributes[attribute.name] = attribute.bool_value
        elif attribute.data_type == "integer":
            attributes[attribute.name] = attribute.int_value
        elif attribute.data_type == "float":
            attributes[attribute.name] = attribute.float_value
        elif attribute.data_type == "enum":
            attributes[attribute.name] = attribute.enum_value
    return attributes


# TODO: migrate the below helper functions into the drawing module, since it is specific to that module


# This function stolen from https://github.com/kevancress/MeasureIt_ARCH/blob/dcf607ce0896aa2284463c6b4ae9cd023fc54cbe/measureit_arch_baseclass.py
# MeasureIt-ARCH is GPL-v3
# In the future I will need to rewrite this to allow the user to have custom
# settings for each annotation object, not read from Blender.
def format_distance(value, isArea=False, hide_units=True):
    s_code = "\u00b2"  # Superscript two THIS IS LEGACY (but being kept for when Area Measurements are re-implimented)

    # Get Scene Unit Settings
    scaleFactor = bpy.context.scene.unit_settings.scale_length
    unit_system = bpy.context.scene.unit_settings.system
    unit_length = bpy.context.scene.unit_settings.length_unit

    toInches = 39.3700787401574887
    inPerFoot = 11.999

    if isArea:
        toInches = 1550
        inPerFoot = 143.999

    value *= scaleFactor

    # Imperial Formating
    if unit_system == "IMPERIAL":
        precision = bpy.context.scene.BIMProperties.imperial_precision
        if precision == "NONE":
            precision = 256
        elif precision == "1":
            precision = 1
        elif "/" in precision:
            precision = int(precision.split("/")[1])

        base = int(precision)
        decInches = value * toInches

        # Seperate ft and inches
        # Unless Inches are the specified Length Unit
        if unit_length != "INCHES":
            feet = math.floor(decInches / inPerFoot)
            decInches -= feet * inPerFoot
        else:
            feet = 0

        # Seperate Fractional Inches
        inches = math.floor(decInches)
        if inches != 0:
            frac = round(base * (decInches - inches))
        else:
            frac = round(base * (decInches))

        # Set proper numerator and denominator
        if frac != base:
            numcycles = int(math.log2(base))
            for i in range(numcycles):
                if frac % 2 == 0:
                    frac = int(frac / 2)
                    base = int(base / 2)
                else:
                    break
        else:
            frac = 0
            inches += 1

        # Check values and compose string
        if inches == 12:
            feet += 1
            inches = 0

        if not isArea:
            tx_dist = ""
            if feet:
                tx_dist += str(feet) + "'"
            if feet and inches:
                tx_dist += " - "
            if inches:
                tx_dist += str(inches)
            if inches and frac:
                tx_dist += " "
            if frac:
                tx_dist += str(frac) + "/" + str(base)
            if inches or frac:
                tx_dist += '"'
        else:
            tx_dist = str("%1.3f" % (value * toInches / inPerFoot)) + " sq. ft."

    # METRIC FORMATING
    elif unit_system == "METRIC":
        precision = bpy.context.scene.BIMProperties.metric_precision
        if precision != 0:
            value = precision * round(float(value) / precision)

        # Meters
        if unit_length == "METERS":
            fmt = "%1.3f"
            if hide_units is False:
                fmt += " m"
            tx_dist = fmt % value
        # Centimeters
        elif unit_length == "CENTIMETERS":
            fmt = "%1.1f"
            if hide_units is False:
                fmt += " cm"
            d_cm = value * (100)
            tx_dist = fmt % d_cm
        # Millimeters
        elif unit_length == "MILLIMETERS":
            fmt = "%1.0f"
            if hide_units is False:
                fmt += " mm"
            d_mm = value * (1000)
            tx_dist = fmt % d_mm

        # Otherwise Use Adaptive Units
        else:
            if round(value, 2) >= 1.0:
                fmt = "%1.3f"
                if hide_units is False:
                    fmt += " m"
                tx_dist = fmt % value
            else:
                if round(value, 2) >= 0.01:
                    fmt = "%1.1f"
                    if hide_units is False:
                        fmt += " cm"
                    d_cm = value * (100)
                    tx_dist = fmt % d_cm
                else:
                    fmt = "%1.0f"
                    if hide_units is False:
                        fmt += " mm"
                    d_mm = value * (1000)
                    tx_dist = fmt % d_mm
        if isArea:
            tx_dist += s_code
    else:
        tx_dist = fmt % value

    return tx_dist


def parse_diagram_scale(camera):
    """Returns numeric value of scale"""
    if camera.BIMCameraProperties.diagram_scale == "CUSTOM":
        _, fraction = camera.BIMCameraProperties.custom_diagram_scale.split("|")
    else:
        _, fraction = camera.BIMCameraProperties.diagram_scale.split("|")
    numerator, denominator = fraction.split("/")
    return float(numerator) / float(denominator)


def get_project_collection(scene):
    """Get main project collection"""

    colls = [c for c in scene.collection.children if c.name.startswith("IfcProject")]
    if len(colls) != 1:
        raise RuntimeError("project collection missing or not unique")
    return colls[0]


def get_active_drawing(scene):
    """Get active drawing collection and camera"""
    props = scene.DocProperties
    if props.active_drawing_index is None or len(props.drawings) == 0:
        return None, None
    try:
        drawing = props.drawings[props.active_drawing_index]
        return scene.collection.children["Views"].children[f"IfcGroup/{drawing.name}"], drawing.camera
    except (KeyError, IndexError):
        raise RuntimeError("missing drawing collection")


def ortho_view_frame(camera, margin=0.015):
    """Calculates 2d bounding box of camera view area.

    Similar to `bpy.types.Camera.view_frame`

    :arg camera: camera of drawing
    :type camera: bpy.types.Camera + BIMCameraProperties
    :arg margin: margins, in scene units
    :type margin: float
    :return: (xmin, xmax, ymin, ymax, zmin, zmax) in local camera coordinates
    """
    aspect = camera.BIMCameraProperties.raster_y / camera.BIMCameraProperties.raster_x
    size = camera.ortho_scale
    hwidth = size * 0.5
    hheight = size * 0.5 * aspect
    scale = parse_diagram_scale(camera)
    xmarg = margin * scale
    ymarg = margin * scale * aspect
    return (-hwidth + xmarg, hwidth - xmarg, -hheight + ymarg, hheight - ymarg, -camera.clip_start, -camera.clip_end)


def almost_zero(v):
    return abs(v) < 1e-5


def clip_segment(bounds, segm):
    """Clipping line segment to bounds

    :arg bounds: (xmin, xmax, ymin, ymax)
    :arg segm: 2 vertices of the segment
    :return: 2 new vertices of segment or None if segment outside the bounding box
    """
    # Liang–Barsky algorithm

    xmin, xmax, ymin, ymax, _, _ = bounds
    p1, p2 = segm

    def clip_side(p, q):
        if almost_zero(p):  # ~= 0, parallel to the side
            if q < 0:
                return None  # outside
            else:
                return 0, 1  # inside

        t = q / p  # the intersection point

        if p < 0:  # entering
            return t, 1
        else:  # leaving
            return 0, t

    dlt = p2 - p1

    tt = (
        clip_side(-dlt.x, p1.x - xmin),  # left
        clip_side(+dlt.x, xmax - p1.x),  # right
        clip_side(-dlt.y, p1.y - ymin),  # bottom
        clip_side(+dlt.y, ymax - p1.y),  # top
    )

    if None in tt:
        return None

    t1 = max(0, max(t[0] for t in tt))
    t2 = min(1, min(t[1] for t in tt))

    if t1 >= t2:
        return None

    p1c = p1 + dlt * t1
    p2c = p1 + dlt * t2

    return p1c, p2c


def elevate_segment(bounds, segm):
    """Elevate line xy-perpendicular segment vertically

    :arg bounds: (xmin, xmax, ymin, ymax)
    :arg segm: 2 vertices of the segment
    :return: 2 new vertices of segment or None if segment outside the bounding box
    """
    _, _, ymin, ymax, zmin, _ = bounds
    p1, p2 = segm
    dlt = p2 - p1
    if not (almost_zero(dlt.x) and almost_zero(dlt.y)):
        return None
    x = p1.x
    return [Vector((x, ymin, zmin)), Vector((x, ymax, zmin))]
