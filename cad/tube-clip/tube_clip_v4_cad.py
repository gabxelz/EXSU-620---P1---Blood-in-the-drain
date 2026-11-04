# EXSU 620 P1 Drain Optics - flow-through clip v4 (5 mm slot, 3.5 mm window, no back wall, 2 mm base, beam 12.2 mm) for IV drip tubing (CadQuery)
# The tube runs vertically through the clip, between the light hole and the sensor.
# Measure the tube's outer diameter with calipers and set tube_od, then run this file.
import cadquery as cq

tube_od = 4.1        # standard IV giving-set tubing is about 4.1 mm OD; MEASURE YOURS
fit = 0.3            # clearance around the tube
board, slot_t = 20.4, 5.0   # v2: slot 3.4 -> 5.0 so the sensor fits with its parts
src_wall, wall, back_wall = 8, 1.2, 2
floor = 2.0          # v4: base under the sensor slot 5.8 -> 2.0 mm
height = 32
beam_z = floor + board / 2   # v4: light path follows the sensor chip (board centre) = 12.2 mm
ap, src_hole = 3.5, 5.2     # v2: window 3 -> 3.5 (stay below the tube bore)

d = tube_od + fit
ch_x = src_wall + wall + d / 2            # tube centre
sens_x = ch_x + d / 2 + wall              # start of sensor slot
bw = board + 0.6
lx = sens_x + slot_t + back_wall
wy = bw + 4
cy = wy / 2

def box(x, y, z, sx, sy, sz):
    return cq.Workplane("XY").box(sx, sy, sz, centered=False).translate((x, y, z))

def xcyl(x0, length, dia, y, z):
    return cq.Workplane("YZ").circle(dia / 2).extrude(length).translate((x0, y, z))

tube_hole = cq.Workplane("XY").circle(d / 2).extrude(height + 2).translate((ch_x, cy, -1))
slit = box(ch_x - tube_od * 0.4, cy, -1, tube_od * 0.8, wy, height + 2)   # push-in slit, tape over it

clip = (box(0, 0, 0, lx, wy, height)
        .cut(tube_hole).cut(slit)
        .cut(xcyl(-1, src_wall + wall + 1, src_hole, cy, beam_z))         # light hole up to the tube
        .cut(xcyl(ch_x, sens_x - ch_x + 1, ap, cy, beam_z))               # window from tube to sensor
        .cut(box(sens_x, cy - bw / 2, beam_z - board / 2, slot_t + back_wall + 1, bw, height)))   # v3: back wall removed, slot open at the back

cq.exporters.export(clip, "tube_clip_v4.step")
cq.exporters.export(clip, "tube_clip_v4.stl", tolerance=0.02, angularTolerance=0.1)
print("tube clip %.1f x %.1f x %.1f mm, tube centre x=%.2f, volume %.0f" % (lx, wy, height, ch_x, clip.val().Volume()))
