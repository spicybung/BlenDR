# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#      *     *       *                 *       *       *         *    #
#  *      //   ) )      *        *       //    ) ) //   ) )           #
#        //___/ /  //  ___   *    __ *  //    / / //___/ /     *      #
#   *   / __  (   // //___) ) //   ) ) //    / / / ___ (              #
#      //    ) ) // //       //   / / //    / / //   | |   *      *   #
#     //____/ / // ((____   //   / / //____/ / //    | |              #
# BlenDR - Blender scripts to work with R* RAGE/openFormat file types #
# 2024 - 2025 SpicyBung                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy_extras.io_utils import ImportHelper


LOD_ORDER = ("high", "med", "low", "vlow")
LOD_SUFFIXES = ("_high", "_med", "_low", "_vlow")


class ImportOpenIVFormats(Operator, ImportHelper):
    bl_idname = "import_scene.openiv_formats"
    bl_label = "Import OpenIV openFormats"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".odr"

    filter_glob: StringProperty(default="*.odr;*.mesh", options={'HIDDEN'}, maxlen=255)

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement
    )

    import_all_lods: BoolProperty(
        name="Import All ODR LODs",
        description="Import high, med, low and vlow meshes referenced by the selected ODR",
        default=True
    )

    apply_odr_materials: BoolProperty(
        name="Use ODR Shader Materials",
        description="Create Blender materials from the shader records in the matching ODR file",
        default=True
    )

    create_bounds: BoolProperty(
        name="Create ODR Bounds",
        description="Create center and AABB helper objects from the ODR file",
        default=True
    )

    limit_material_name: BoolProperty(
        name="Limit Material Names to 20 Characters",
        description="Keeps material names under the older OpenIV-friendly length used by this importer",
        default=True
    )

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        selected_files = [file_elem.name for file_elem in self.files]

        if not selected_files:
            selected_files = [os.path.basename(self.filepath)]

        imported_count = 0

        for selected_file in selected_files:
            filepath = os.path.join(directory, selected_file)
            extension = os.path.splitext(selected_file)[1].lower()

            try:
                if extension == ".odr":
                    imported_count += self.import_odr(context, filepath)
                elif extension == ".mesh":
                    imported_count += self.import_mesh_with_matching_odr(context, filepath)
                else:
                    self.report({'WARNING'}, f"Skipped unsupported OpenIV openFormat file: {selected_file}")

            except Exception as error:
                self.report({'ERROR'}, f"Error importing {selected_file}: {error}")

        if imported_count == 0:
            return {'CANCELLED'}

        self.report({'INFO'}, f"Imported {imported_count} OpenIV openFormat mesh object(s).")
        return {'FINISHED'}

    def import_odr(self, context, odr_filepath):
        directory = os.path.dirname(odr_filepath)
        base_name = os.path.splitext(os.path.basename(odr_filepath))[0]
        odr_data = self.parse_odr_file(odr_filepath)
        collection = self.create_collection(context, f"{base_name}.odr")

        imported_count = 0
        lod_items = self.get_lod_items(odr_data)

        if not self.import_all_lods and lod_items:
            lod_items = lod_items[:1]

        if not lod_items:
            guessed_mesh = os.path.join(directory, f"{base_name}_high.mesh")
            if not os.path.exists(guessed_mesh):
                guessed_mesh = os.path.join(directory, f"{base_name}.mesh")
            lod_items = [("high", {"mesh_file": os.path.basename(guessed_mesh), "distance": None})]

        for lod_name, lod_data in lod_items:
            mesh_file = lod_data.get("mesh_file")
            if not mesh_file:
                continue

            mesh_filepath = os.path.join(directory, mesh_file)
            if not os.path.exists(mesh_filepath):
                self.report({'WARNING'}, f"Missing {lod_name} mesh referenced by {os.path.basename(odr_filepath)}: {mesh_file}")
                continue

            obj = self.import_mesh_file(context, mesh_filepath, collection, odr_data, lod_name)
            if obj:
                imported_count += 1

        if self.create_bounds:
            self.create_odr_helpers(collection, odr_data, base_name)

        return imported_count

    def import_mesh_with_matching_odr(self, context, mesh_filepath):
        directory = os.path.dirname(mesh_filepath)
        mesh_name = os.path.basename(mesh_filepath)
        base_mesh_name = os.path.splitext(mesh_name)[0]
        odr_filepath = self.find_matching_odr(directory, base_mesh_name)
        odr_data = self.parse_odr_file(odr_filepath) if odr_filepath else self.empty_odr_data()
        collection_name = os.path.basename(odr_filepath) if odr_filepath else f"{base_mesh_name}.mesh"
        collection = self.create_collection(context, collection_name)
        lod_name = self.get_lod_name_from_mesh_name(base_mesh_name)

        obj = self.import_mesh_file(context, mesh_filepath, collection, odr_data, lod_name)

        if obj and self.create_bounds and odr_filepath:
            self.create_odr_helpers(collection, odr_data, os.path.splitext(os.path.basename(odr_filepath))[0])

        if odr_filepath:
            self.report({'INFO'}, f"Imported {mesh_name} with matching {os.path.basename(odr_filepath)} data applied.")
        else:
            self.report({'WARNING'}, f"Imported {mesh_name} but no matching .odr file found.")

        return 1 if obj else 0

    def import_mesh_file(self, context, mesh_filepath, collection, odr_data, lod_name):
        vertices, faces, mesh_materials = self.parse_mesh_file(mesh_filepath)
        vertices = self.ensure_valid_vertices(vertices)
        faces = self.ensure_valid_faces(faces, len(vertices))

        mesh_name = os.path.splitext(os.path.basename(mesh_filepath))[0]
        mesh = bpy.data.meshes.new(name=mesh_name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        obj = bpy.data.objects.new(name=mesh_name, object_data=mesh)
        obj["openiv_lod"] = lod_name

        lod_info = odr_data.get("lods", {}).get(lod_name)
        if lod_info and lod_info.get("distance") is not None:
            obj["openiv_lod_distance"] = lod_info["distance"]

        collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        for material_name in mesh_materials:
            material = self.get_or_create_material(material_name)
            if not self.mesh_has_material(mesh, material.name):
                mesh.materials.append(material)

        if self.apply_odr_materials:
            self.apply_odr_data_to_mesh(obj, odr_data)

        return obj

    def mesh_has_material(self, mesh, material_name):
        return any(material and material.name == material_name for material in mesh.materials)

    def create_collection(self, context, collection_name):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            collection = bpy.data.collections.new(name=collection_name)
            context.scene.collection.children.link(collection)
        return collection

    def get_lod_items(self, odr_data):
        lods = odr_data.get("lods", {})
        items = []

        for lod_name in LOD_ORDER:
            lod_data = lods.get(lod_name)
            if lod_data:
                items.append((lod_name, lod_data))

        return items

    def find_matching_odr(self, directory, base_mesh_name):
        odr_base_name = base_mesh_name

        for suffix in LOD_SUFFIXES:
            if odr_base_name.endswith(suffix):
                odr_base_name = odr_base_name[: -len(suffix)]
                break

        odr_filepath = os.path.join(directory, f"{odr_base_name}.odr")
        if os.path.exists(odr_filepath):
            return odr_filepath

        return None

    def get_lod_name_from_mesh_name(self, base_mesh_name):
        for lod_name in LOD_ORDER:
            if base_mesh_name.endswith(f"_{lod_name}"):
                return lod_name
        return "high"

    def ensure_valid_vertices(self, vertices):
        valid_vertices = [vertex for vertex in vertices if self.is_valid_vertex(vertex)]

        if not valid_vertices:
            return [(0.0, 0.0, 0.0)]

        for index, vertex in enumerate(vertices):
            if not self.is_valid_vertex(vertex):
                nearest_valid = valid_vertices[-1]
                vertices[index] = (nearest_valid[0] + 0.1, nearest_valid[1] + 0.1, nearest_valid[2] + 0.1)

        return vertices

    def ensure_valid_faces(self, faces, vertex_count):
        valid_faces = [face for face in faces if self.is_valid_face(face, vertex_count)]

        if not valid_faces:
            if vertex_count >= 3:
                return [(0, 1, 2)]
            return []

        for index, face in enumerate(faces):
            if not self.is_valid_face(face, vertex_count):
                faces[index] = valid_faces[-1]

        return faces

    def is_valid_vertex(self, vertex):
        return isinstance(vertex, tuple) and len(vertex) == 3 and all(isinstance(coord, float) for coord in vertex)

    def is_valid_face(self, face, vertex_count):
        return isinstance(face, tuple) and len(face) >= 3 and all(isinstance(index, int) and 0 <= index < vertex_count for index in face[:3])

    def parse_mesh_file(self, filepath):
        vertices = []
        faces = []
        materials = []
        reading_vertices = False
        reading_faces = False

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()

        if not lines or not lines[0].strip().startswith("Version"):
            raise ValueError("Unsupported .mesh file. Missing Version line.")

        for line in lines[1:]:
            stripped_line = line.strip()

            if not stripped_line:
                continue

            if stripped_line.startswith("Verts"):
                reading_vertices = True
                reading_faces = False
                continue

            if stripped_line.startswith("Idx"):
                reading_faces = True
                reading_vertices = False
                continue

            if stripped_line.startswith("Material"):
                material_name = self.read_mesh_material_name(stripped_line)
                if material_name:
                    materials.append(material_name)
                continue

            if stripped_line == "}":
                reading_vertices = False
                reading_faces = False
                continue

            if reading_vertices:
                vertex = self.read_mesh_vertex(stripped_line)
                if vertex:
                    vertices.append(vertex)
                continue

            if reading_faces:
                face = self.read_mesh_face(stripped_line)
                if face:
                    faces.append(face)

        return vertices, faces, materials

    def read_mesh_vertex(self, line):
        position_text = line.split('/', 1)[0].strip()
        parts = position_text.split()

        if len(parts) < 3:
            return None

        try:
            return (float(parts[0]), float(parts[1]), float(parts[2]))
        except ValueError:
            return None

    def read_mesh_face(self, line):
        face_indices = []

        for part in line.replace(',', ' ').split():
            try:
                face_indices.append(int(part))
            except ValueError:
                pass

        if len(face_indices) >= 3:
            return (face_indices[0], face_indices[1], face_indices[2])

        return None

    def read_mesh_material_name(self, line):
        parts = line.split()
        if len(parts) < 2:
            return None

        material_name = os.path.splitext(os.path.basename(parts[1].replace('\\', os.sep)))[0]
        return self.clean_material_name(material_name)

    def parse_odr_file(self, filepath):
        data = self.empty_odr_data()
        current_shader = None

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("Version"):
                    parts = line.split()
                    data["version"] = parts[1] if len(parts) > 1 else None
                    continue

                if line.startswith("Shaders"):
                    continue

                if line.startswith("{"):
                    current_shader = {}
                    continue

                if line.startswith("}"):
                    if current_shader:
                        data["shaders"].append(current_shader)
                    current_shader = None
                    continue

                if current_shader is not None:
                    shader = self.read_odr_shader(line)
                    if shader:
                        current_shader.update(shader)
                    continue

                lod = self.read_odr_lod(line)
                if lod:
                    lod_name, lod_data = lod
                    data["lods"][lod_name] = lod_data
                    continue

                if line.startswith("center"):
                    data["center"] = self.read_vector_line(line)
                    continue

                if line.startswith("AABBMin"):
                    data["bounding_box"]["min"] = self.read_vector_line(line)
                    continue

                if line.startswith("AABBMax"):
                    data["bounding_box"]["max"] = self.read_vector_line(line)
                    continue

                if line.startswith("radius"):
                    parts = line.split()
                    data["radius"] = self.to_float(parts[1]) if len(parts) > 1 else None

        return data

    def empty_odr_data(self):
        return {
            "version": None,
            "shaders": [],
            "lods": {},
            "bounding_box": {},
            "center": None,
            "radius": None
        }

    def read_odr_shader(self, line):
        parts = line.split()
        if len(parts) < 2:
            return None

        shader_name = parts[0]
        full_material_path = parts[1]
        material_name = os.path.splitext(os.path.basename(full_material_path.replace('\\', os.sep)))[0]
        params = [self.to_float(part, part) for part in parts[2:]]

        return {
            "shader_name": shader_name,
            "material_name": self.clean_material_name(material_name),
            "params": params
        }

    def read_odr_lod(self, line):
        parts = line.split()
        if len(parts) < 2 or parts[0] not in LOD_ORDER:
            return None

        lod_name = parts[0]
        mesh_file = parts[1]
        distance = self.to_float(parts[2]) if len(parts) > 2 else None
        return lod_name, {"mesh_file": mesh_file, "distance": distance}

    def read_vector_line(self, line):
        parts = line.split()[1:4]
        if len(parts) != 3:
            return None
        return tuple(self.to_float(part, 0.0) for part in parts)

    def apply_odr_data_to_mesh(self, mesh_obj, data):
        for shader_info in data.get("shaders", []):
            material = self.create_material(shader_info)
            if not self.mesh_has_material(mesh_obj.data, material.name):
                mesh_obj.data.materials.append(material)

        if data.get("radius") is not None:
            mesh_obj["openiv_radius"] = data["radius"]

    def create_odr_helpers(self, collection, data, base_name):
        center = data.get("center")
        bounds = data.get("bounding_box", {})
        min_coords = bounds.get("min")
        max_coords = bounds.get("max")

        if center:
            center_empty = bpy.data.objects.new(f"{base_name}_center", None)
            center_empty.empty_display_type = 'SPHERE'
            center_empty.empty_display_size = 0.25
            center_empty.location = center
            collection.objects.link(center_empty)

        if min_coords and max_coords:
            box_mesh = self.create_aabb_mesh(f"{base_name}_aabb_mesh", min_coords, max_coords)
            box_obj = bpy.data.objects.new(f"{base_name}_aabb", box_mesh)
            box_obj.display_type = 'WIRE'
            collection.objects.link(box_obj)

    def create_aabb_mesh(self, mesh_name, min_coords, max_coords):
        min_x, min_y, min_z = min_coords
        max_x, max_y, max_z = max_coords
        vertices = [
            (min_x, min_y, min_z),
            (min_x, min_y, max_z),
            (min_x, max_y, min_z),
            (min_x, max_y, max_z),
            (max_x, min_y, min_z),
            (max_x, min_y, max_z),
            (max_x, max_y, min_z),
            (max_x, max_y, max_z),
        ]
        edges = [
            (0, 1), (0, 2), (0, 4),
            (3, 1), (3, 2), (3, 7),
            (5, 1), (5, 4), (5, 7),
            (6, 2), (6, 4), (6, 7),
        ]
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(vertices, edges, [])
        mesh.update()
        return mesh

    def create_material(self, shader_info):
        material_name = shader_info.get("material_name") or "default_material"
        material = self.get_or_create_material(material_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        nodes.clear()

        shader = nodes.new(type="ShaderNodeBsdfPrincipled")
        params = shader_info.get("params", [])
        roughness = params[0] if len(params) > 0 and isinstance(params[0], float) else 1.0
        metallic = params[1] if len(params) > 1 and isinstance(params[1], float) else 0.0

        if "Roughness" in shader.inputs:
            shader.inputs["Roughness"].default_value = roughness
        if "Metallic" in shader.inputs:
            shader.inputs["Metallic"].default_value = metallic

        material_output = nodes.new(type="ShaderNodeOutputMaterial")
        material.node_tree.links.new(shader.outputs["BSDF"], material_output.inputs["Surface"])
        return material

    def get_or_create_material(self, material_name):
        material_name = self.clean_material_name(material_name)
        material = bpy.data.materials.get(material_name)
        if material is None:
            material = bpy.data.materials.new(name=material_name)
        return material

    def clean_material_name(self, material_name):
        if not material_name:
            material_name = "default_material"
        if self.limit_material_name:
            material_name = material_name[:20]
        return material_name

    def to_float(self, value, fallback=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback



ImportMeshWithODR = ImportOpenIVFormats


def menu_func_import(self, context):
    self.layout.operator(ImportOpenIVFormats.bl_idname, text="OpenIV openFormats (.odr/.mesh)")


def register():
    bpy.utils.register_class(ImportOpenIVFormats)


def unregister():
    bpy.utils.unregister_class(ImportOpenIVFormats)


if __name__ == "__main__":
    register()
