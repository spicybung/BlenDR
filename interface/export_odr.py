# BlenDR - Blender scripts to work with RAGE/openFormat file types 
# 2024 - 2025 SpicyBung

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import bpy
from mathutils import Vector
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty

#######################################################
class ExportODR(Operator, ExportHelper):
    bl_idname = "export_scene.odr"
    bl_label = "Export ODR File"
    filename_ext = ".odr"

    filter_glob: StringProperty(default="*.odr", options={'HIDDEN'})

    include_center: BoolProperty(
        name="Include Center",
        description="Include object center in ODR file",
        default=True
    )

    include_radius: BoolProperty(
        name="Include Radius",
        description="Include object radius in ODR file",
        default=True
    )
    #######################################################
    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected.")
            return {'CANCELLED'}

        filepath = self.filepath
        if not filepath.endswith(".odr"):
            filepath += ".odr"

        with open(filepath, 'w') as f:
            f.write("Version 8\n")
            f.write("Shaders {}\n".format(len(selected_objects)))

            for obj in selected_objects:
                material_name = obj.data.materials[0].name if obj.data.materials else "default_material"
                f.write("{\n")
                f.write(f"    normal {material_name} 1.0 0.0\n")
                f.write("}\n")

            for obj in selected_objects:
                lod = "high"  # Default LOD name
                name = obj.name
                if "_low" in name:
                    lod = "low"
                elif "_med" in name:
                    lod = "med"
                elif "_vlow" in name:
                    lod = "vlow"
                mesh_file = f"{name}.mesh"
                distance = 50.0 if lod == "high" else 100.0
                f.write(f"{lod} {mesh_file} {distance:.1f}\n")

            if self.include_center:
                bbox_center = self.get_center(context, selected_objects)
                f.write("center {:.6f} {:.6f} {:.6f}\n".format(*bbox_center))

            bbox_min, bbox_max = self.get_bounding_box_extents(selected_objects)
            f.write("AABBMin {:.6f} {:.6f} {:.6f}\n".format(*bbox_min))
            f.write("AABBMax {:.6f} {:.6f} {:.6f}\n".format(*bbox_max))

            if self.include_radius:
                radius = (Vector(bbox_max) - Vector(bbox_min)).length / 2
                f.write(f"radius {radius:.6f}\n")

        self.report({'INFO'}, f"ODR exported: {filepath}")
        return {'FINISHED'}
    #######################################################
    def get_center(self, context, objects):
        min_v, max_v = self.get_bounding_box_extents(objects)
        return tuple((min_v[i] + max_v[i]) / 2 for i in range(3))
    #######################################################
    def get_bounding_box_extents(self, objects):
        min_coord = Vector((float('inf'), float('inf'), float('inf')))
        max_coord = Vector((float('-inf'), float('-inf'), float('-inf')))
        for obj in objects:
            for v in obj.bound_box:
                world_v = obj.matrix_world @ Vector(v)
                min_coord = Vector(map(min, min_coord, world_v))
                max_coord = Vector(map(max, max_coord, world_v))
        return tuple(min_coord), tuple(max_coord)
    #######################################################
def menu_func_export(self, context):
    self.layout.operator(ExportODR.bl_idname, text="Export ODR File (.odr)")

def register():
    bpy.utils.register_class(ExportODR)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportODR)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
