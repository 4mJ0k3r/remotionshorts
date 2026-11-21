"""Small set and pose fixes identified in the v2 stills."""
def polish(s, key, material, label):
    import bpy
    objects=bpy.data.objects
    for name, colors in [('Grass field',((.046,.14,.032,1),(.20,.35,.065,1))),('Foreground dirt road',((.22,.086,.032,1),(.52,.27,.11,1)))]:
        obj=objects[name]
        mat=material('Cinematic '+name,colors[0][:3])
        obj.data.materials[0]=mat
        tree=mat.node_tree
        noise=tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=2.2
        noise.inputs['Detail'].default_value=5
        coord=tree.nodes.new('ShaderNodeTexCoord')
        tree.links.new(coord.outputs['Object'],noise.inputs['Vector'])
        ramp=tree.nodes.new('ShaderNodeValToRGB')
        for stop,color in zip(ramp.color_ramp.elements,colors):
            stop.color=color
        tree.links.new(noise.outputs['Fac'],ramp.inputs[0])
        shader=tree.nodes.get('Principled BSDF')
        tree.links.new(ramp.outputs[0],shader.inputs['Base Color'])
        bump=tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=.32
        bump.inputs['Distance'].default_value=.075
        tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        tree.links.new(bump.outputs[0],shader.inputs['Normal'])
    for obj in s.objects:
        if obj.name.startswith('char_you_') and obj.animation_data and any('_'+pose+'_' in obj.name for pose in ('happy','belly')):
            for curve in obj.animation_data.action.fcurves:
                if curve.data_path=='scale':
                    for point in curve.keyframe_points:
                        if abs(point.co.x-210)<.01:
                            point.co.x=198
                    curve.update()
    key(objects['Ignored cheque on grass'],'location',2095,(1.46,-.45,.13))
