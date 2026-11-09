import bpy
import math
import os

def build_scene():
    print("=== STARTING ANTIGRAVITY 2.5D DEMO SCENE BUILD (REFINED) ===")

    # 1. Clean scene completely
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    # 2. RULE 1: BLENDER 4.2 RENDER CONTRACT & HARDWARE SAFETY
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.use_raytracing = False
    scene.render.use_simplify = True
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 180
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'

    # Video output settings
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
    scene.render.filepath = "D:/remotionshorts/out/antigravity_demo/exam_demo.mp4"

    # 3. Setup World Environment & Lighting
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.94, 0.90, 0.84, 1.0) # warm ambient
        bg_node.inputs["Strength"].default_value = 0.85

    # Sunlight streaming from classroom windows (+X, +Y)
    sun_data = bpy.data.lights.new(name="SunLight", type='SUN')
    sun_data.energy = 2.6
    sun_data.color = (1.0, 0.96, 0.90)
    sun_obj = bpy.data.objects.new(name="SunLight", object_data=sun_data)
    sun_obj.location = (5.0, 1.0, 4.0)
    sun_obj.rotation_euler = (math.radians(45), math.radians(25), math.radians(-50))
    bpy.context.collection.objects.link(sun_obj)

    # Soft fill light
    fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
    fill_data.energy = 140.0
    fill_data.color = (0.95, 0.95, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    fill_obj.location = (-1.0, -1.0, 2.5)
    bpy.context.collection.objects.link(fill_obj)

    # 4. RULE 2: CEL SHADER FACTORY
    def load_img(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required image: {path}")
        img = bpy.data.images.load(filepath=path, check_existing=False)
        img.reload()
        return img

    SPRITE_DIR = "D:/remotionshorts/output/sprites"
    hero_calm_img = load_img(os.path.join(SPRITE_DIR, "hero_calm.png"))
    hero_oops_img = load_img(os.path.join(SPRITE_DIR, "hero_oops.png"))
    hero_panic_img = load_img(os.path.join(SPRITE_DIR, "hero_panic.png"))
    crush_write_img = load_img(os.path.join(SPRITE_DIR, "crush_write.png"))
    crush_glare_img = load_img(os.path.join(SPRITE_DIR, "crush_glare.png"))
    stink_img = load_img(os.path.join(SPRITE_DIR, "stink_ribbon.png"))
    sweat_img = load_img(os.path.join(SPRITE_DIR, "sweat_drop.png"))

    def create_single_cel_mat(name, img, emission_strength=1.12):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        mat.blend_method = 'CLIP'
        mat.shadow_method = 'CLIP'
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (800, 0)

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader.location = (600, 0)

        transp = nodes.new("ShaderNodeBsdfTransparent")
        transp.location = (350, 100)

        emission = nodes.new("ShaderNodeEmission")
        emission.location = (350, -100)
        emission.inputs["Strength"].default_value = emission_strength

        math_alpha = nodes.new("ShaderNodeMath")
        math_alpha.operation = 'GREATER_THAN'
        math_alpha.inputs[1].default_value = 0.72
        math_alpha.location = (350, 250)

        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        tex_node.location = (0, 0)

        links.new(tex_node.outputs["Alpha"], math_alpha.inputs[0])
        links.new(math_alpha.outputs["Value"], mix_shader.inputs["Fac"])
        links.new(tex_node.outputs["Color"], emission.inputs["Color"])
        links.new(transp.outputs["BSDF"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])

        return mat

    def create_hero_mat():
        mat = bpy.data.materials.new(name="MAT_Hero")
        mat.use_nodes = True
        mat.blend_method = 'CLIP'
        mat.shadow_method = 'CLIP'
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (1100, 0)

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader.location = (900, 0)

        transp = nodes.new("ShaderNodeBsdfTransparent")
        transp.location = (650, 100)

        emission = nodes.new("ShaderNodeEmission")
        emission.location = (650, -100)
        emission.inputs["Strength"].default_value = 1.12

        math_alpha = nodes.new("ShaderNodeMath")
        math_alpha.operation = 'GREATER_THAN'
        math_alpha.inputs[1].default_value = 0.72
        math_alpha.location = (650, 250)

        tex_calm = nodes.new("ShaderNodeTexImage")
        tex_calm.name = "TexCalm"
        tex_calm.image = hero_calm_img
        tex_calm.location = (0, 300)

        tex_oops = nodes.new("ShaderNodeTexImage")
        tex_oops.name = "TexOops"
        tex_oops.image = hero_oops_img
        tex_oops.location = (0, 0)

        tex_panic = nodes.new("ShaderNodeTexImage")
        tex_panic.name = "TexPanic"
        tex_panic.image = hero_panic_img
        tex_panic.location = (0, -300)

        mix_col_1 = nodes.new("ShaderNodeMix")
        mix_col_1.name = "MixCol_Oops"
        mix_col_1.data_type = 'RGBA'
        mix_col_1.location = (300, 100)
        links.new(tex_calm.outputs["Color"], mix_col_1.inputs[6])
        links.new(tex_oops.outputs["Color"], mix_col_1.inputs[7])

        mix_col_2 = nodes.new("ShaderNodeMix")
        mix_col_2.name = "MixCol_Panic"
        mix_col_2.data_type = 'RGBA'
        mix_col_2.location = (450, 50)
        links.new(mix_col_1.outputs[2], mix_col_2.inputs[6])
        links.new(tex_panic.outputs["Color"], mix_col_2.inputs[7])
        links.new(mix_col_2.outputs[2], emission.inputs["Color"])

        mix_alpha_1 = nodes.new("ShaderNodeMix")
        mix_alpha_1.name = "MixAlpha_Oops"
        mix_alpha_1.data_type = 'FLOAT'
        mix_alpha_1.location = (300, 350)
        links.new(tex_calm.outputs["Alpha"], mix_alpha_1.inputs[2])
        links.new(tex_oops.outputs["Alpha"], mix_alpha_1.inputs[3])

        mix_alpha_2 = nodes.new("ShaderNodeMix")
        mix_alpha_2.name = "MixAlpha_Panic"
        mix_alpha_2.data_type = 'FLOAT'
        mix_alpha_2.location = (450, 300)
        links.new(mix_alpha_1.outputs[0], mix_alpha_2.inputs[2])
        links.new(tex_panic.outputs["Alpha"], mix_alpha_2.inputs[3])
        links.new(mix_alpha_2.outputs[0], math_alpha.inputs[0])

        links.new(math_alpha.outputs["Value"], mix_shader.inputs["Fac"])
        links.new(transp.outputs["BSDF"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])

        for node in [mix_col_1, mix_alpha_1]:
            fac = node.inputs[0]
            fac.default_value = 0.0
            fac.keyframe_insert("default_value", frame=1)
            fac.keyframe_insert("default_value", frame=35)
            fac.default_value = 1.0
            fac.keyframe_insert("default_value", frame=36)
            fac.keyframe_insert("default_value", frame=95)

        for node in [mix_col_2, mix_alpha_2]:
            fac = node.inputs[0]
            fac.default_value = 0.0
            fac.keyframe_insert("default_value", frame=1)
            fac.keyframe_insert("default_value", frame=95)
            fac.default_value = 1.0
            fac.keyframe_insert("default_value", frame=96)
            fac.keyframe_insert("default_value", frame=180)

        if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
            for fcurve in mat.node_tree.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

        return mat

    def create_crush_mat():
        mat = bpy.data.materials.new(name="MAT_Crush")
        mat.use_nodes = True
        mat.blend_method = 'CLIP'
        mat.shadow_method = 'CLIP'
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node = nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (900, 0)

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader.location = (700, 0)

        transp = nodes.new("ShaderNodeBsdfTransparent")
        transp.location = (450, 100)

        emission = nodes.new("ShaderNodeEmission")
        emission.location = (450, -100)
        emission.inputs["Strength"].default_value = 1.12

        math_alpha = nodes.new("ShaderNodeMath")
        math_alpha.operation = 'GREATER_THAN'
        math_alpha.inputs[1].default_value = 0.72
        math_alpha.location = (450, 250)

        tex_write = nodes.new("ShaderNodeTexImage")
        tex_write.image = crush_write_img
        tex_write.location = (0, 200)

        tex_glare = nodes.new("ShaderNodeTexImage")
        tex_glare.image = crush_glare_img
        tex_glare.location = (0, -200)

        mix_col = nodes.new("ShaderNodeMix")
        mix_col.name = "MixCol_Crush"
        mix_col.data_type = 'RGBA'
        mix_col.location = (250, -50)
        links.new(tex_write.outputs["Color"], mix_col.inputs[6])
        links.new(tex_glare.outputs["Color"], mix_col.inputs[7])
        links.new(mix_col.outputs[2], emission.inputs["Color"])

        mix_alpha = nodes.new("ShaderNodeMix")
        mix_alpha.name = "MixAlpha_Crush"
        mix_alpha.data_type = 'FLOAT'
        mix_alpha.location = (250, 200)
        links.new(tex_write.outputs["Alpha"], mix_alpha.inputs[2])
        links.new(tex_glare.outputs["Alpha"], mix_alpha.inputs[3])
        links.new(mix_alpha.outputs[0], math_alpha.inputs[0])

        links.new(math_alpha.outputs["Value"], mix_shader.inputs["Fac"])
        links.new(transp.outputs["BSDF"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])

        for node in [mix_col, mix_alpha]:
            fac = node.inputs[0]
            fac.default_value = 0.0
            fac.keyframe_insert("default_value", frame=1)
            fac.keyframe_insert("default_value", frame=74)
            fac.default_value = 1.0
            fac.keyframe_insert("default_value", frame=75)
            fac.keyframe_insert("default_value", frame=180)

        if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
            for fcurve in mat.node_tree.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

        return mat

    mat_hero = create_hero_mat()
    mat_crush = create_crush_mat()
    mat_stink = create_single_cel_mat("MAT_Stink", stink_img, emission_strength=2.2)
    mat_sweat = create_single_cel_mat("MAT_Sweat", sweat_img, emission_strength=1.4)

    # 5. Helper to create a vertical 2D Cel Card (Facing -Y)
    def create_character_card(name, width, height, mat):
        mesh = bpy.data.meshes.new(name=name + "_Mesh")
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        hw = width / 2.0
        verts = [
            (-hw, 0.0, 0.0),    # 0: bottom-left
            (hw, 0.0, 0.0),     # 1: bottom-right
            (hw, 0.0, height),  # 2: top-right
            (-hw, 0.0, height)  # 3: top-left
        ]
        faces = [(0, 1, 2, 3)]
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        uv_layer = mesh.uv_layers.new(name="UVMap")
        uv_data = uv_layer.data
        uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        for i, loop in enumerate(mesh.loops):
            uv_data[i].uv = uvs[loop.vertex_index]

        obj.data.materials.append(mat)
        bpy.context.collection.objects.link(obj)
        return obj

    # HERO_CARD: Placed at (X = -0.35, Y = 0.0, Z = 0.0)
    hero_card = create_character_card("HERO_CARD", 1.1, 1.65, mat_hero)
    hero_card.location = (-0.35, 0.0, 0.0)

    # CRUSH_CARD: Placed at (X = 0.95, Y = 1.85, Z = 0.0)
    # Staggered behind and to the right so both are 100% visible in 3/4 view!
    crush_card = create_character_card("CRUSH_CARD", 1.1, 1.65, mat_crush)
    crush_card.location = (0.95, 1.85, 0.0)

    # 6. RULE 4: ANIMATE HERO_CARD SQUASH & STRETCH (ZERO JELLY WOBBLE!)
    scale_keys = [
        (1, (1.0, 1.0, 1.0)),
        (35, (1.0, 1.0, 1.0)),
        (36, (1.0, 1.0, 1.0)),
        (39, (1.08, 1.0, 0.92)),
        (42, (0.95, 1.0, 1.06)),
        (45, (1.0, 1.0, 1.0)),
        (95, (1.0, 1.0, 1.0)),
        (96, (1.0, 1.0, 1.0)),
        (99, (0.93, 1.0, 1.08)),
        (103, (1.0, 1.0, 1.0)),
        (180, (1.0, 1.0, 1.0))
    ]
    for frame, sc in scale_keys:
        hero_card.scale = sc
        hero_card.keyframe_insert("scale", frame=frame)

    if hero_card.animation_data and hero_card.animation_data.action:
        for fcurve in hero_card.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                if kf.co[0] in [1, 35, 45, 95, 103, 180]:
                    kf.interpolation = 'BEZIER'
                    kf.handle_left_type = 'AUTO_CLAMPED'
                    kf.handle_right_type = 'AUTO_CLAMPED'

    crush_card.scale = (1.0, 1.0, 1.0)
    crush_card.keyframe_insert("scale", frame=1)
    crush_card.keyframe_insert("scale", frame=180)

    # 7. WAVY GREEN STINK RIBBONS (STINK_1..3)
    stink_ribbons = []
    stink_start_data = [
        ("STINK_1", (-0.35, 0.15, 0.40), (0.45, 1.55, 0.85), 0.45, 1.10),
        ("STINK_2", (-0.20, 0.22, 0.35), (0.75, 1.65, 0.95), 0.38, 1.00),
        ("STINK_3", (-0.45, 0.18, 0.45), (0.95, 1.75, 1.15), 0.42, 1.15),
    ]
    for sname, start_loc, end_loc, sw, sh in stink_start_data:
        s_obj = create_character_card(sname, sw, sh, mat_stink)
        s_obj.location = start_loc
        stink_ribbons.append(s_obj)

        s_obj.scale = (0.0, 0.0, 0.0)
        s_obj.keyframe_insert("scale", frame=1)
        s_obj.keyframe_insert("scale", frame=35)

        s_obj.location = start_loc
        s_obj.keyframe_insert("location", frame=42)
        s_obj.scale = (0.01, 0.01, 0.01)
        s_obj.keyframe_insert("scale", frame=42)

        s_obj.scale = (1.0, 1.0, 1.0)
        s_obj.keyframe_insert("scale", frame=55)

        s_obj.location = end_loc
        s_obj.keyframe_insert("location", frame=95)
        s_obj.scale = (1.0, 1.0, 1.0)
        s_obj.keyframe_insert("scale", frame=95)

        s_obj.location = (end_loc[0] + 0.05, end_loc[1] + 0.1, end_loc[2] + 0.15)
        s_obj.keyframe_insert("location", frame=180)
        s_obj.scale = (1.0, 1.0, 1.0)
        s_obj.keyframe_insert("scale", frame=180)

    # 8. SHOT 2 SWEAT DROPLET CARDS (SWEAT_1..3)
    sweat_drops = []
    sweat_anim_data = [
        # (name, p_start, p_peak, p_end, f_start)
        ("SWEAT_1", (-0.46, -0.03, 1.34), (-0.52, -0.04, 1.40), (-0.55, -0.05, 1.25), 98),
        ("SWEAT_2", (-0.20, -0.03, 1.34), (-0.12, -0.04, 1.44), (-0.06, -0.05, 1.28), 98),
        ("SWEAT_3", (-0.32, -0.03, 1.44), (-0.26, -0.04, 1.54), (-0.22, -0.05, 1.36), 100),
    ]
    for wname, p_start, p_peak, p_end, f_start in sweat_anim_data:
        # Centered card for sweat drop
        w_mesh = bpy.data.meshes.new(name=wname + "_Mesh")
        w_obj = bpy.data.objects.new(name=wname, object_data=w_mesh)
        sw_size = 0.18
        hw = sw_size / 2.0
        w_verts = [(-hw, 0.0, -hw), (hw, 0.0, -hw), (hw, 0.0, hw), (-hw, 0.0, hw)]
        w_faces = [(0, 1, 2, 3)]
        w_mesh.from_pydata(w_verts, [], w_faces)
        w_mesh.update()

        uv_layer = w_mesh.uv_layers.new(name="UVMap")
        uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        for i, loop in enumerate(w_mesh.loops):
            uv_layer.data[i].uv = uvs[loop.vertex_index]

        w_obj.data.materials.append(mat_sweat)
        bpy.context.collection.objects.link(w_obj)
        sweat_drops.append(w_obj)

        # Frame 1..f_start-1: hidden
        w_obj.location = p_start
        w_obj.scale = (0.0, 0.0, 0.0)
        w_obj.keyframe_insert("scale", frame=1)
        w_obj.keyframe_insert("scale", frame=f_start - 1)

        # Pop out
        w_obj.location = p_start
        w_obj.scale = (1.0, 1.0, 1.0)
        w_obj.keyframe_insert("location", frame=f_start)
        w_obj.keyframe_insert("scale", frame=f_start)

        # Parabolic peak
        f_mid = f_start + 12
        w_obj.location = p_peak
        w_obj.keyframe_insert("location", frame=f_mid)
        w_obj.scale = (1.15, 1.15, 1.15)
        w_obj.keyframe_insert("scale", frame=f_mid)

        # Fall & shrink
        w_obj.location = p_end
        w_obj.keyframe_insert("location", frame=135)
        w_obj.scale = (0.0, 0.0, 0.0)
        w_obj.keyframe_insert("scale", frame=135)

        w_obj.scale = (0.0, 0.0, 0.0)
        w_obj.keyframe_insert("scale", frame=180)

    # 9. RULE 3: 3D EXAM HALL SET
    def create_diffuse_mat(name, color, roughness=0.5, specular=0.3):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0) if len(color) == 3 else color
            bsdf.inputs["Roughness"].default_value = roughness
            if "Specular IOR Level" in bsdf.inputs:
                bsdf.inputs["Specular IOR Level"].default_value = specular
        return mat

    mat_wood = create_diffuse_mat("MAT_Wood", (0.38, 0.22, 0.10), roughness=0.35)
    mat_metal = create_diffuse_mat("MAT_DarkMetal", (0.15, 0.15, 0.16), roughness=0.45)
    mat_paper = create_diffuse_mat("MAT_ExamPaper", (0.96, 0.95, 0.92), roughness=0.8)
    mat_blackboard = create_diffuse_mat("MAT_Blackboard", (0.07, 0.16, 0.11), roughness=0.7)
    mat_teal_wall = create_diffuse_mat("MAT_TealWall", (0.11, 0.34, 0.32), roughness=0.6)
    mat_cream_wall = create_diffuse_mat("MAT_CreamWall", (0.94, 0.90, 0.82), roughness=0.7)

    # Floor
    mat_floor = bpy.data.materials.new(name="MAT_CheckeredFloor")
    mat_floor.use_nodes = True
    f_nodes = mat_floor.node_tree.nodes
    f_links = mat_floor.node_tree.links
    f_nodes.clear()

    f_out = f_nodes.new("ShaderNodeOutputMaterial")
    f_bsdf = f_nodes.new("ShaderNodeBsdfPrincipled")
    f_checker = f_nodes.new("ShaderNodeTexChecker")
    f_checker.inputs["Scale"].default_value = 6.0
    f_checker.inputs["Color1"].default_value = (0.88, 0.82, 0.74, 1.0)
    f_checker.inputs["Color2"].default_value = (0.34, 0.28, 0.25, 1.0)

    f_links.new(f_checker.outputs["Color"], f_bsdf.inputs["Base Color"])
    f_bsdf.inputs["Roughness"].default_value = 0.32
    if "Specular IOR Level" in f_bsdf.inputs:
        f_bsdf.inputs["Specular IOR Level"].default_value = 0.4
    f_links.new(f_bsdf.outputs["BSDF"], f_out.inputs["Surface"])

    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 2.0, 0.0))
    floor_obj = bpy.context.active_object
    floor_obj.name = "Floor"
    floor_obj.data.materials.append(mat_floor)

    # Back Wall (Y = 5.2m)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 5.2, 0.6))
    wall_lower = bpy.context.active_object
    wall_lower.name = "Wall_Lower_Teal"
    wall_lower.scale = (8.4, 1.0, 1.2)
    wall_lower.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    wall_lower.data.materials.append(mat_teal_wall)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.18, 1.2))
    rail = bpy.context.active_object
    rail.name = "Dado_Rail"
    rail.scale = (8.4, 0.06, 0.08)
    rail.data.materials.append(mat_wood)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 5.2, 2.5))
    wall_upper = bpy.context.active_object
    wall_upper.name = "Wall_Upper_Cream"
    wall_upper.scale = (8.4, 1.0, 2.6)
    wall_upper.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    wall_upper.data.materials.append(mat_cream_wall)

    # Side walls
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-4.2, 2.0, 1.9))
    wall_left = bpy.context.active_object
    wall_left.name = "Wall_Left"
    wall_left.scale = (1.0, 8.4, 3.8)
    wall_left.rotation_euler = (0, math.radians(90), 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    wall_left.data.materials.append(mat_cream_wall)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.2, 2.0, 1.9))
    wall_right = bpy.context.active_object
    wall_right.name = "Wall_Right"
    wall_right.scale = (1.0, 8.4, 3.8)
    wall_right.rotation_euler = (0, math.radians(-90), 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    wall_right.data.materials.append(mat_cream_wall)

    # Blackboard frame (wood) behind at Y = 5.16m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.16, 2.1))
    bb_frame = bpy.context.active_object
    bb_frame.name = "Blackboard_Frame"
    bb_frame.scale = (4.52, 0.04, 1.42)
    bb_frame.data.materials.append(mat_wood)

    # Dark-green Blackboard slate in front of frame at Y = 5.13m!
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.13, 2.1))
    bb_obj = bpy.context.active_object
    bb_obj.name = "Blackboard"
    bb_obj.scale = (4.35, 0.02, 1.28)
    bb_obj.data.materials.append(mat_blackboard)

    # Blackboard header sign
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.11, 2.62))
    header_bar = bpy.context.active_object
    header_bar.name = "Blackboard_Sign"
    header_bar.scale = (3.2, 0.02, 0.16)
    mat_sign = create_diffuse_mat("MAT_Sign", (0.95, 0.93, 0.88), roughness=0.5)
    header_bar.data.materials.append(mat_sign)

    # Spinning 3D Ceiling Fan at (0, 1.5, 3.4)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.16, location=(0.0, 1.5, 3.4))
    fan_hub = bpy.context.active_object
    fan_hub.name = "Ceiling_Fan_Hub"
    fan_hub.data.materials.append(mat_metal)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.4, location=(0.0, 1.5, 3.6))
    fan_rod = bpy.context.active_object
    fan_rod.name = "Ceiling_Fan_Rod"
    fan_rod.data.materials.append(mat_metal)

    for angle_deg in [0, 90, 180, 270]:
        rad = math.radians(angle_deg)
        bx = 0.45 * math.cos(rad)
        by = 1.5 + 0.45 * math.sin(rad)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 3.4))
        blade = bpy.context.active_object
        blade.name = f"FanBlade_{angle_deg}"
        blade.scale = (0.75, 0.16, 0.015)
        blade.rotation_euler = (0, 0, rad)
        blade.data.materials.append(mat_wood)
        blade.parent = fan_hub

    fan_hub.rotation_euler = (0, 0, 0)
    fan_hub.keyframe_insert("rotation_euler", frame=1)
    fan_hub.rotation_euler = (0, 0, 12 * 2 * math.pi)
    fan_hub.keyframe_insert("rotation_euler", frame=180)
    if fan_hub.animation_data and fan_hub.animation_data.action:
        for fcurve in fan_hub.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    # 10. SCHOOL DESKS
    def create_school_desk(prefix, desk_x, desk_y, tabletop_z=0.52):
        desk_parts = []
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(desk_x, desk_y, tabletop_z - 0.015))
        top = bpy.context.active_object
        top.name = f"{prefix}_DeskTop"
        top.scale = (0.85, 0.48, 0.03)
        top.data.materials.append(mat_wood)
        desk_parts.append(top)

        leg_dx = 0.38
        leg_dy = 0.20
        leg_h = tabletop_z - 0.03
        for lx, ly in [(-leg_dx, -leg_dy), (leg_dx, -leg_dy), (-leg_dx, leg_dy), (leg_dx, leg_dy)]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=leg_h, location=(desk_x + lx, desk_y + ly, leg_h / 2.0))
            leg = bpy.context.active_object
            leg.name = f"{prefix}_Leg"
            leg.data.materials.append(mat_metal)
            desk_parts.append(leg)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(desk_x, desk_y, tabletop_z - 0.12))
        shelf = bpy.context.active_object
        shelf.name = f"{prefix}_Shelf"
        shelf.scale = (0.78, 0.42, 0.015)
        shelf.data.materials.append(mat_metal)
        desk_parts.append(shelf)

        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(desk_x - 0.08, desk_y, tabletop_z + 0.002))
        paper = bpy.context.active_object
        paper.name = f"{prefix}_Paper"
        paper.scale = (0.24, 0.32, 1.0)
        paper.rotation_euler = (0, 0, math.radians(6))
        paper.data.materials.append(mat_paper)
        desk_parts.append(paper)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.18, location=(desk_x + 0.16, desk_y, tabletop_z + 0.005))
        pencil = bpy.context.active_object
        pencil.name = f"{prefix}_Pencil"
        pencil.rotation_euler = (math.radians(90), 0, math.radians(20))
        mat_pencil = create_diffuse_mat("MAT_PencilYellow", (0.95, 0.75, 0.15))
        pencil.data.materials.append(mat_pencil)
        desk_parts.append(pencil)

        return desk_parts

    # Hero desk at (-0.35, -0.22, 0.0)
    hero_desk = create_school_desk("HERO", -0.35, -0.22, tabletop_z=0.52)
    # Crush desk at (0.95, 1.60, 0.0)
    crush_desk = create_school_desk("CRUSH", 0.95, 1.60, tabletop_z=0.52)

    # 11. RULE 4: CAMERA & BEAT-DRIVEN 2-SHOT SETUP
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 35.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = hero_card
    cam_data.dof.aperture_fstop = 1.8

    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_target = bpy.data.objects.new("CAM_TARGET", None)
    bpy.context.collection.objects.link(cam_target)

    track = cam_obj.constraints.new(type='TRACK_TO')
    track.target = cam_target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # Shot 1 Camera Motion (Frames 1–95):
    # Smooth 3/4 diagonal push-in:
    # Frame 1: loc = (-1.65, -2.85, 1.35), target = (0.05, 0.6, 0.85)
    # Frame 95: loc = (-1.35, -2.35, 1.28), target = (0.05, 0.6, 0.85)
    cam_obj.location = (-1.65, -2.85, 1.35)
    cam_obj.keyframe_insert("location", frame=1)
    cam_obj.location = (-1.35, -2.35, 1.28)
    cam_obj.keyframe_insert("location", frame=95)

    cam_target.location = (0.05, 0.6, 0.85)
    cam_target.keyframe_insert("location", frame=1)
    cam_target.keyframe_insert("location", frame=95)

    cam_data.lens = 35.0
    cam_data.keyframe_insert("lens", frame=1)
    cam_data.keyframe_insert("lens", frame=95)

    # Shot 2 Camera Cut & Zoom-Punch (Frames 96–180):
    # Frame 96 (Constant cut):
    # loc = (-0.75, -1.35, 1.18), target = (-0.12, 0.4, 1.02)
    cam_obj.location = (-0.75, -1.35, 1.18)
    cam_obj.keyframe_insert("location", frame=96)
    cam_obj.keyframe_insert("location", frame=180)

    cam_target.location = (-0.12, 0.4, 1.02)
    cam_target.keyframe_insert("location", frame=96)
    cam_target.keyframe_insert("location", frame=180)

    # Focal length: 42mm (f=96) -> 54mm (f=101) -> 50mm (f=104) -> hold through 180
    cam_data.lens = 42.0
    cam_data.keyframe_insert("lens", frame=96)
    cam_data.lens = 54.0
    cam_data.keyframe_insert("lens", frame=101)
    cam_data.lens = 50.0
    cam_data.keyframe_insert("lens", frame=104)
    cam_data.lens = 50.0
    cam_data.keyframe_insert("lens", frame=180)

    for obj_with_anim in [cam_obj, cam_target]:
        if obj_with_anim.animation_data and obj_with_anim.animation_data.action:
            for fcurve in obj_with_anim.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    if kf.co[0] == 95:
                        kf.interpolation = 'CONSTANT'

    if cam_data.animation_data and cam_data.animation_data.action:
        for fcurve in cam_data.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                if kf.co[0] == 95:
                    kf.interpolation = 'CONSTANT'

    # 12. Save .blend file
    blend_path = "D:/remotionshorts/output/blender/antigravity_demo.blend"
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"=== SCENE REBUILT AND SAVED TO {blend_path} ===")

build_scene()
