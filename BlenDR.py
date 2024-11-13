import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, CollectionProperty

class ImportMeshWithODR(Operator, ImportHelper):
    """Import multiple .mesh files and apply matching .odr data if available"""
    bl_idname = "import_scene.mesh_with_odr"
    bl_label = "Import Mesh with ODR Data"
    filename_ext = ".mesh"
    filter_glob: StringProperty(default="*.mesh", options={'HIDDEN'}, maxlen=255)
    
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement
    )
    
    # Option to limit material name length to 20 characters
    limit_material_name: BoolProperty(
        name="Limit Material Name to 20 Characters",
        description="If enabled, limits material names to 20 characters",
        default=True
    )

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        
        # Process each selected file
        for file_elem in self.files:
            mesh_filename = file_elem.name
            base_mesh_name, _ = os.path.splitext(mesh_filename)
            mesh_filepath = os.path.join(directory, mesh_filename)

            # Create a collection for this .mesh file
            collection_name = f"{base_mesh_name}.odr"
            new_collection = bpy.data.collections.new(name=collection_name)
            context.scene.collection.children.link(new_collection)

            # Check for suffixes and derive the corresponding .odr filename without it
            odr_filename = f"{base_mesh_name}.odr"
            for suffix in ["_high", "_med", "_low", "_vlow"]:
                if base_mesh_name.endswith(suffix):
                    odr_filename = f"{base_mesh_name[: -len(suffix)]}.odr"
                    break

            # Parse and import the .mesh file
            try:
                vertices, faces, materials = self.parse_mesh_file(mesh_filepath)

                # Ensure vertices and faces are structured and add placeholders for missing data
                vertices = self.ensure_valid_vertices(vertices)
                faces = self.ensure_valid_faces(faces, len(vertices))

                # Debugging output to inspect vertices and faces
                print(f"Processing {mesh_filename} - Validated Vertices: {vertices}, Validated Faces: {faces}")

                # Create mesh and object in Blender
                mesh = bpy.data.meshes.new(name=base_mesh_name)
                mesh.from_pydata(vertices, [], faces)
                mesh.update()

                obj = bpy.data.objects.new(name=base_mesh_name, object_data=mesh)
                new_collection.objects.link(obj)  # Link the object to the new collection
                context.view_layer.objects.active = obj
                obj.select_set(True)

                # Add materials to the mesh
                for material_name in materials:
                    # Truncate the material name to 20 characters if option is enabled
                    if self.limit_material_name:
                        material_name = material_name[:20]
                        print(f"Truncated Material Name: {material_name} (Length: {len(material_name)})")

                    # Check if the truncated material already exists in Blender; if not, create it
                    material = bpy.data.materials.get(material_name)
                    if not material:
                        material = bpy.data.materials.new(name=material_name)
                    
                    # Add the truncated material to the mesh
                    mesh.materials.append(material)

                # Check if the derived odr_filename exists
                odr_filepath = os.path.join(directory, odr_filename)
                if os.path.exists(odr_filepath):
                    odr_data = self.parse_odr_file(odr_filepath)
                    self.apply_data_to_mesh(obj, odr_data, new_collection)  # Pass new_collection to handle additional elements
                    self.report({'INFO'}, f"Imported {mesh_filename} with matching {odr_filename} data applied.")
                else:
                    self.report({'WARNING'}, f"Imported {mesh_filename} but no matching .odr file found.")

            except Exception as e:
                self.report({'ERROR'}, f"Error reading file {mesh_filename}: {e}")

        return {'FINISHED'}

    def ensure_valid_vertices(self, vertices):
        """Ensure vertices are valid and add placeholders for missing data."""
        valid_vertices = [v for v in vertices if isinstance(v, tuple) and len(v) == 3 and all(isinstance(coord, float) for coord in v)]
        
        # If no valid vertices, start with a placeholder vertex
        if not valid_vertices:
            return [(0.0, 0.0, 0.0)]

        for i, v in enumerate(vertices):
            if not (isinstance(v, tuple) and len(v) == 3 and all(isinstance(coord, float) for coord in v)):
                # If invalid, replace with a placeholder near the last valid vertex
                nearest_valid = valid_vertices[-1]
                placeholder = (nearest_valid[0] + 0.1, nearest_valid[1] + 0.1, nearest_valid[2] + 0.1)
                vertices[i] = placeholder
                print(f"Replaced invalid vertex at index {i} with placeholder {placeholder}")

        return vertices

    def ensure_valid_faces(self, faces, vertex_count):
        """Ensure faces are valid and add placeholders for missing data."""
        valid_faces = [f for f in faces if isinstance(f, tuple) and len(f) == 3 and all(isinstance(idx, int) and idx < vertex_count for idx in f)]
        
        # If no valid faces, start with a placeholder face
        if not valid_faces:
            return [(0, 0, 0)]

        for i, f in enumerate(faces):
            if not (isinstance(f, tuple) and len(f) == 3 and all(isinstance(idx, int) and idx < vertex_count for idx in f)):
                # Replace with a face using the first three vertices as a placeholder
                faces[i] = (0, 1, 2)
                print(f"Replaced invalid face at index {i} with placeholder face (0, 1, 2)")

        return faces

    def parse_mesh_file(self, filepath):
        """Parse .mesh file and return vertices, faces, and materials."""
        vertices = []
        faces = []
        materials = []
        reading_vertices = False
        reading_faces = False

        with open(filepath, 'r') as f:
            lines = f.readlines()
            if not lines or lines[0].strip() != "Version 11 13":
                raise ValueError("Unsupported version. Expected 'Version 11 13'.")

            for line in lines[1:]:
                stripped_line = line.strip()

                if stripped_line.startswith("Verts"):
                    reading_vertices = True
                    continue

                elif stripped_line.startswith("Idx"):
                    reading_faces = True
                    reading_vertices = False
                    continue

                elif stripped_line.startswith("Material"):
                    material_name = stripped_line.split()[1]
                    # Strip out anything after a period (e.g., ".dds")
                    if '.' in material_name:
                        material_name = material_name.split('.')[0]
                    # Truncate material name length if option is enabled
                    if self.limit_material_name:
                        material_name = material_name[:20]
                    # Ensure only valid, non-numeric material names are added
                    if material_name and not material_name.isdigit():
                        materials.append(material_name)
                    else:
                        print(f"Skipping invalid material name: {material_name}")  # Debugging line
                    continue

                elif stripped_line == "}":
                    reading_vertices = False
                    reading_faces = False
                    continue

                if reading_vertices:
                    if '/' in stripped_line:
                        vert_data = stripped_line.split('/')
                        try:
                            position = tuple(map(float, vert_data[0].strip().split()))
                            vertices.append(position)
                        except ValueError:
                            print(f"Skipping invalid vertex data: {vert_data[0]}")  # Debugging line

                elif reading_faces:
                    face_indices = [int(idx) for idx in stripped_line.split() if idx.isdigit()]
                    if len(face_indices) >= 3:
                        faces.append((face_indices[0], face_indices[1], face_indices[2]))

        return vertices, faces, materials

    def parse_odr_file(self, filepath):
        """Parse .odr file and return relevant data for materials and shaders."""
        data = {
            "version": None,
            "shaders": [],
            "lods": {},
            "bounding_box": {},
            "center": None,
            "radius": None
        }
        current_shader = None

        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()

                if line.startswith("Version"):
                    data["version"] = line.split(" ")[1]

                elif line.startswith("Shaders"):
                    shader_count = int(line.split(" ")[1])

                elif line.startswith("{"):
                    current_shader = {}

                elif line.startswith("}"):
                    if current_shader:
                        data["shaders"].append(current_shader)
                        current_shader = None

                elif current_shader is not None:
                    parts = line.split(" ")
                    shader_name = parts[0]
                    full_material_path = parts[1]
                    material_name = full_material_path.split("\\")[-1].split('.')[0]

                    # Truncate material name length if option is enabled
                    if self.limit_material_name:
                        material_name = material_name[:20]
                    print(f"Parsed ODR Material Name: {material_name} (Length: {len(material_name)})")  # Debugging line

                    shader_params = [float(param) if param.replace('.', '', 1).isdigit() else param for param in parts[2:]]

                    current_shader = {
                        "shader_name": shader_name,
                        "material_name": material_name,
                        "params": shader_params
                    }

                elif line.startswith("high") or line.startswith("med") or line.startswith("low") or line.startswith("vlow"):
                    parts = line.split(" ", 2)
                    lod_name = parts[0]
                    mesh_file = parts[1]
                    distance = float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '', 1).isdigit() else None
                    data["lods"][lod_name] = {"mesh_file": mesh_file, "distance": distance}

                elif line.startswith("center"):
                    data["center"] = tuple(map(float, line.split()[1:]))

                elif line.startswith("AABBMin"):
                    data["bounding_box"]["min"] = tuple(map(float, line.split()[1:]))

                elif line.startswith("AABBMax"):
                    data["bounding_box"]["max"] = tuple(map(float, line.split()[1:]))

                elif line.startswith("radius"):
                    data["radius"] = float(line.split()[1])

        return data

    def apply_data_to_mesh(self, mesh_obj, data, collection):
        """Applies parsed ODR data to the selected mesh object in Blender."""
        for shader_info in data.get('shaders', []):
            material = self.create_material(shader_info)
            if material.name not in mesh_obj.data.materials:
                mesh_obj.data.materials.append(material)

        if "center" in data:
            center_empty = bpy.data.objects.new("BoundingCenter", None)
            center_empty.location = data["center"]
            collection.objects.link(center_empty)
            mesh_obj.parent = center_empty

        if "bounding_box" in data:
            if "min" in data["bounding_box"] and "max" in data["bounding_box"]:
                min_coords = data["bounding_box"]["min"]
                max_coords = data["bounding_box"]["max"]
                bb_verts = [
                    (min_coords[0], min_coords[1], min_coords[2]),
                    (min_coords[0], min_coords[1], max_coords[2]),
                    (min_coords[0], max_coords[1], min_coords[2]),
                    (min_coords[0], max_coords[1], max_coords[2]),
                    (max_coords[0], min_coords[1], min_coords[2]),
                    (max_coords[0], min_coords[1], max_coords[2]),
                    (max_coords[0], max_coords[1], min_coords[2]),
                    (max_coords[0], max_coords[1], max_coords[2]),
                ]
                for coord in bb_verts:
                    empty = bpy.ops.object.empty_add(type='PLAIN_AXES', location=coord)
                    collection.objects.link(empty)  # Link bounding box empties to the collection

    def create_material(self, shader_info):
        material_name = shader_info["material_name"]
        if material_name in bpy.data.materials:
            return bpy.data.materials[material_name]

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()

        shader = nodes.new(type="ShaderNodeBsdfPrincipled")
        roughness = shader_info["params"][0] if len(shader_info["params"]) > 0 and isinstance(shader_info["params"][0], float) else 1.0
        metallic = shader_info["params"][1] if len(shader_info["params"]) > 1 and isinstance(shader_info["params"][1], float) else 0.0
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic

        material_output = nodes.new(type="ShaderNodeOutputMaterial")
        material.node_tree.links.new(shader.outputs["BSDF"], material_output.inputs["Surface"])

        return material

# Registering the operator
def menu_func_import(self, context):
    self.layout.operator(ImportMeshWithODR.bl_idname, text="Import Mesh with ODR Data")

def register():
    bpy.utils.register_class(ImportMeshWithODR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportMeshWithODR)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
