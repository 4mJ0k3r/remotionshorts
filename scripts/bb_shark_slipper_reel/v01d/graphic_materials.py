"""Version-local graphic ink and hard-band shading for the approved cast."""
import ricks_v2_kit as k


def matte(material, roughness=1., specular=0., metallic=0.):
    for shader in material.node_tree.nodes:
        if shader.type=="BSDF_PRINCIPLED":
            shader.inputs["Roughness"].default_value=roughness
            shader.inputs["Specular IOR Level"].default_value=specular
            shader.inputs["Metallic"].default_value=metallic


def output(material):
    return next(node for node in material.node_tree.nodes if node.type=="OUTPUT_MATERIAL")


def light_value(material):
    nodes,links=material.node_tree.nodes,material.node_tree.links
    diffuse=nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.name="White matte received-light probe"
    diffuse.inputs["Color"].default_value=(1,1,1,1)
    shade=nodes.new("ShaderNodeShaderToRGB")
    luma=nodes.new("ShaderNodeRGBToBW")
    links.new(diffuse.outputs[0],shade.inputs[0])
    links.new(shade.outputs[0],luma.inputs[0])
    return luma.outputs[0]


def bands(material, stops, source=None, label="Graphic cel bands • .04 transitions"):
    nodes,links=material.node_tree.nodes,material.node_tree.links
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.label=label
    k.look._ramp(ramp,stops,"EASE")
    links.new(light_value(material) if source is None else source,ramp.inputs[0])
    return ramp.outputs["Color"]


def emission_output(material,color,strength=1.,alpha=None):
    n,l=material.node_tree.nodes,material.node_tree.links
    em=n.new("ShaderNodeEmission")
    em.label="Graphic paint"
    l.new(color,em.inputs[0])
    em.inputs[1].default_value=strength
    shader=em.outputs[0]
    if alpha is not None:
        clear=n.new("ShaderNodeBsdfTransparent")
        mix=n.new("ShaderNodeMixShader")
        l.new(alpha,mix.inputs[0])
        l.new(clear.outputs[0],mix.inputs[1])
        l.new(shader,mix.inputs[2])
        shader=mix.outputs[0]
    l.new(shader,output(material).inputs[0])


def face(material, shadow, boundary, hood_frame):
    matte(material)
    light=light_value(material)
    if hood_frame is not None:
        n,l=material.node_tree.nodes,material.node_tree.links
        generated,split=n.new("ShaderNodeTexCoord"),n.new("ShaderNodeSeparateXYZ")
        l.new(generated.outputs["Generated"],split.inputs[0])
        art_fill=n.new("ShaderNodeMapRange")
        art_fill.label="Lower-face painted bounce under the hood"
        art_fill.inputs["From Min"].default_value=.40
        art_fill.inputs["From Max"].default_value=.62
        art_fill.inputs["To Min"].default_value=.59
        art_fill.inputs["To Max"].default_value=.07
        l.new(split.outputs["Z"],art_fill.inputs["Value"])
        active=n.new("ShaderNodeMath")
        active.operation="MULTIPLY"
        l.new(art_fill.outputs[0],active.inputs[0])
        for f,value in ((1,0.),(hood_frame-1,0.),(hood_frame,1.)):
            active.inputs[1].default_value=value
            active.inputs[1].keyframe_insert("default_value",frame=f)
        channel=material.node_tree.animation_data.action.fcurves.find(
            active.inputs[1].path_from_id("default_value"))
        for key in channel.keyframe_points:
            key.interpolation="CONSTANT"
        shaped=n.new("ShaderNodeMath")
        shaped.operation="MAXIMUM"
        l.new(active.outputs[0],shaped.inputs[0])
        l.new(light,shaped.inputs[1])
        light=shaped.outputs[0]
    color=bands(material,[(0.,shadow),(boundary,shadow),(boundary+.04,"#FFF9F0"),
                          (1.,"#FFF9F0")],light)
    emission_output(material,color,1.48)


def graphics(material, darkness=.24, texture=True, tee=False, two_tone=False):
    """Preserve pigment/UV artwork while stepping the fill at the key boundary."""
    matte(material)
    n,l=material.node_tree.nodes,material.node_tree.links
    p=next(node for node in n if node.type=="BSDF_PRINCIPLED")
    image=next((node for node in n if node.type=="TEX_IMAGE"),None)
    alpha=image.outputs["Alpha"] if image else None
    base=p.inputs["Base Color"]
    if tee and image is None:
        coord=n.new("ShaderNodeTexCoord")
        split=n.new("ShaderNodeSeparateXYZ")
        stripe=n.new("ShaderNodeValToRGB")
        k.look._ramp(stripe,[(0.,"#777a86"),(.333,"#efece0"),(1.,"#efece0")],
                     "CONSTANT")
        l.new(coord.outputs["Generated"],split.inputs[0])
        l.new(split.outputs["Z"],stripe.inputs[0])
        color=stripe.outputs[0]
    elif base.is_linked:
        color=base.links[0].from_socket
    else:
        constant=n.new("ShaderNodeRGB")
        constant.outputs[0].default_value=base.default_value
        color=constant.outputs[0]
    if not texture:
        emission_output(material,color,.98,alpha)
        return
    stops=[(0.,"#777f9b"),(darkness,"#777f9b"),(darkness+.04,"#ffffff")]
    stops.extend([(1.,"#ffffff")] if two_tone else
                 [(.58,"#ffffff"),(.62,"#fff1de"),(1.,"#fff1de")])
    tint=bands(material,stops)
    mix=n.new("ShaderNodeMixRGB")
    mix.blend_type="MULTIPLY"
    mix.inputs[0].default_value=1
    l.new(color,mix.inputs[1])
    l.new(tint,mix.inputs[2])
    emission_output(material,mix.outputs[0],1.23,alpha)


def apply_cast(love,scout,hood_frame):
    ink=k.emission("Jet-black character contour • #040407","#040407",1.0)
    ink.use_backface_culling=True
    legs=k.emission("Jet-black stick limbs • #06060A","#06060A",1.0)
    handled=set()
    for actor in (love,scout):
        actor_materials={m for obj in actor.root.children_recursive
                         if obj.type in {"MESH","CURVE"} for m in obj.data.materials if m}
        for mat in actor_materials:
            matte(mat)
        for mod in actor.ink_modifiers:
            mod.id_data.data.materials[0]=ink
        for limb in (*actor.legs,*actor.arms):
            limb.data.materials[0]=legs
        for obj in actor.root.children_recursive:
            if not obj.type in {"MESH","CURVE"} or not obj.data.materials:
                continue
            mat=obj.data.materials[0]
            if mat in handled or not any(n.type=="BSDF_PRINCIPLED" for n in mat.node_tree.nodes):
                continue
            name=obj.name
            if "ellipsoid head" in name:
                face(mat,"#9BB0D4" if actor is love else "#B4C2DA",
                     .31 if actor is love else .39,hood_frame if actor is love else None)
            elif obj in actor.expressions.values():
                graphics(mat,texture=False)
            else:
                graphics(mat,darkness=.28,tee=actor is scout and "pill torso" in name,
                         two_tone=mat.name.startswith("Scout • swept black"))
            handled.add(mat)
    return ink
