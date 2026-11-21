"""A closed garment surface with sleeves sewn to the torso vertex loops."""
from collections import Counter
import math

from mathutils import Vector


SIDES = 20
RINGS = (.10, .21, .33, .45, .58, .71, .82, .88, .93, .96)


def shoulder_loop(center):
    left, right = center - 2, center + 2
    return ([(3, i % SIDES) for i in range(left, right + 1)]
            + [(4, right % SIDES)]
            + [(5, i % SIDES) for i in range(right, left - 1, -1)]
            + [(4, left % SIDES)])


def create(name, profile, fabric, seam, parent, geometry):
    verts = [(rx * math.cos(i * math.tau / SIDES), ry * math.sin(i * math.tau / SIDES), z)
             for z, rx, ry in profile for i in range(SIDES)]
    shoulder_segments = {(center + j) % SIDES for center in (0, SIDES // 2) for j in range(-2, 2)}
    faces = [tuple(reversed(range(SIDES))), tuple(range(len(verts) - SIDES, len(verts)))]
    for row in range(len(profile) - 1):
        for i in range(SIDES):
            if row in (3, 4) and i in shoulder_segments:
                continue
            a = row * SIDES + i
            b = row * SIDES + (i + 1) % SIDES
            faces.append((a, b, b + SIDES, a + SIDES))

    # Compact unused vertices in the openings. Keeping loose points would make
    # the exported garment non-manifold even though the surface is sewn closed.
    used = sorted({i for face in faces for i in face})
    remap = {old: new for new, old in enumerate(used)}
    verts = [verts[i] for i in used]
    faces = [tuple(remap[i] for i in face) for face in faces]
    folds = []
    bindings = {}
    for side in (-1, 1):
        previous = [remap[row * SIDES + i] for row, i in shoulder_loop(0 if side == 1 else SIDES // 2)]
        opening = [Vector(verts[i]) for i in previous]
        middle = sum(opening, Vector()) / len(opening)
        samples = [(v.y - middle.y, v.z - middle.z) for v in opening]
        bindings[side] = (len(verts), middle, samples)
        for row, fraction in enumerate(RINGS):
            current = list(range(len(verts), len(verts) + len(previous)))
            for i, (y, z) in enumerate(samples):
                verts.append((middle.x + side * fraction * .34, middle.y + y * .55, middle.z + z * .55))
                j = (i + 1) % len(previous)
                if row == len(RINGS) - 2:
                    folds.append(len(faces))
                faces.append((previous[i], previous[j], current[j], current[i]))
            previous = current
        faces.append(tuple(previous))
    garment = geometry.mesh(name, verts, faces, fabric, parent)
    edge_uses = Counter(tuple(sorted((a, b))) for face in faces
                        for a, b in zip(face, (*face[1:], face[0])))
    if any(count != 2 for count in edge_uses.values()):
        raise ValueError(f'{name} does not have a closed garment surface')
    garment.data.materials.append(seam)
    for index in folds:
        garment.data.polygons[index].material_index = 1
    for side, (start, middle, samples) in bindings.items():
        garment[f'sleeve_start_{side}'] = start
        garment[f'sleeve_center_{side}'] = tuple(middle)
        garment[f'sleeve_section_{side}'] = [item for pair in samples for item in pair]
    smooth = garment.modifiers.new('Continuous cotton surface', 'SUBSURF')
    smooth.levels = smooth.render_levels = 2
    return garment


def pose(garment, side, arm_points, body_matrix):
    local_space = body_matrix.inverted_safe()
    path = [local_space @ p for p in arm_points]
    start = garment[f'sleeve_start_{side}']
    origin = Vector(garment[f'sleeve_center_{side}'])
    angles = list(garment[f'sleeve_section_{side}'])
    section = [Vector((0, y * 1.55, z)).normalized() for y, z in zip(angles[::2], angles[1::2])]
    axis = Vector((side, 0, 0))
    turn = None
    width = .059 if garment.name.startswith('Papa') else .065
    for ring, fraction in enumerate(RINGS):
        index = fraction * (len(path) - 1)
        whole = int(index)
        center = path[whole].lerp(path[whole + 1], index - whole)
        direction = (path[min(whole + 2, len(path) - 1)] - path[max(0, whole - 1)]).normalized()
        if ring < 3:
            blend = (.27, .58, .88)[ring]
            shoulder = origin + axis * (.045 + .069 * ring)
            center = shoulder.lerp(center, blend)
            direction = axis.lerp(direction, blend).normalized()
        if turn is None:
            turn = axis.rotation_difference(direction)
        else:
            turn = previous_direction.rotation_difference(direction) @ turn
        previous_direction = direction
        radius = width * (1 - .36 * fraction) * (1.04 if ring == 7 else 1)
        for vertex, radial in enumerate(section):
            garment.data.vertices[start + ring * len(section) + vertex].co = center + turn @ radial * radius
    garment.data.update()
