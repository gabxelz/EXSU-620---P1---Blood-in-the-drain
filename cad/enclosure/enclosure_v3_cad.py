# EXSU 620 P1 Drain Optics - electronics case v3 (team table rows 2-4) (CadQuery)
#   T6_caseA_base_v1  152 x 94 x 50.0  front panel: ack button + speaker grille with the speaker inside; cable ports in the ends
#   T6_caseA_lid_v1   152 x 94 x 6.6   light window, NeoPixel ring holder, snap fit (file is upside down)
#   T6_light_cap_v1    44 x 44 x 15.3  translucent diffuser over the light window (open side up)
import cadquery as cq, math

ox, oy, oh = 152.0, 94.0, 50.0
wall, floor = 2.0, 2.0
in_x, in_y = ox - 2 * wall, oy - 2 * wall
cy = oy / 2
lid_t, lid_h = 2.0, 6.6                # lid plate + snap lip = 6.6
lip_h, lip_t, fit = lid_h - lid_t, 1.2, 0.25
snap_r, snap_z, snap_len = 0.45, 2.3, 30.0   # bump on the lip, groove in the wall, 2.3 below the rim

usb_w, usb_d = 13.0, 30.0              # left end, micro-USB
sens_w, sens_d = 10.0, 14.0            # right end, sensor 1 and sensor 2 cables
spk_od, spk_lip = 45.0, 2.0            # speaker inside, held behind the grille by a locating ring (fits up to 45 mm)
btn_x, btn_z, btn_d = 130.0, 25.0, 16.2           # front panel, panel-mount ack button
grille_x, grille_z, grille_d, grille_hole = 88.0, 25.0, 36.0, 2.2   # front panel speaker grille

ring_x, ring_od, ring_r = wall + 32.0, 44.5, 19.1  # NeoPixel Ring 16 under the light window
win_d = 41.0                           # light window: shows all 16 LEDs
cap, cap_h, cap_wall, cap_top = 44.0, 15.3, 1.6, 1.2
spig_h, spig_t = 2.5, 1.2              # cap spigot drops into the light window

def box(x, y, z, sx, sy, sz):
    return cq.Workplane("XY").box(sx, sy, sz, centered=False).translate((x, y, z))

def zcyl(x, y, z, dia, h):
    return cq.Workplane("XY").circle(dia / 2).extrude(h).translate((x, y, z))

def ycyl(x, y, z, dia, h):            # axis along +Y from y
    return cq.Workplane("XZ").circle(dia / 2).extrude(-h).translate((x, y, z))

def xbar(x, y, z, length, dia):       # horizontal rod along X
    return cq.Workplane("YZ").circle(dia / 2).extrude(length).translate((x, y, z))

# ---- base ----
base = box(0, 0, 0, ox, oy, oh).edges("|Z").fillet(4.0)
base = base.cut(box(wall, wall, floor, in_x, in_y, oh))
base = base.cut(box(-1, cy - usb_w / 2, oh - usb_d, wall + 2, usb_w, usb_d + 1))
for y in (cy - 14, cy + 14):
    base = base.cut(box(ox - wall - 1, y - sens_w / 2, oh - sens_d, wall + 2, sens_w, sens_d + 1))
spk_ring = ycyl(grille_x, wall - 0.01, grille_z, spk_od + 0.6 + 2 * 1.2, spk_lip).cut(ycyl(grille_x, wall - 1, grille_z, spk_od + 0.6, spk_lip + 2))
base = base.union(spk_ring)
base = base.cut(ycyl(btn_x, -1, btn_z, btn_d, wall + 2))
pitch = grille_hole + 1.6
n = int(grille_d / pitch) + 1
for i in range(-n, n + 1):
    for j in range(-n, n + 1):
        x = grille_x + i * pitch + (j % 2) * pitch / 2
        z = grille_z + j * pitch * 0.866
        if (x - grille_x) ** 2 + (z - grille_z) ** 2 <= (grille_d / 2) ** 2:
            base = base.cut(ycyl(x, -1, z, grille_hole, wall + 2))
for y in (wall, oy - wall):            # snap grooves in the inside of both long walls
    base = base.cut(xbar(ox / 2 - snap_len / 2 - 1, y, oh - snap_z, snap_len + 2, 2 * snap_r + 0.3))

# ---- lid, modelled in place on top of the base ----
lid = box(0, 0, oh, ox, oy, lid_t).edges("|Z").fillet(4.0)
lx0, ly0, lsx, lsy = wall + fit, wall + fit, in_x - 2 * fit, in_y - 2 * fit
lip = box(lx0, ly0, oh - lip_h, lsx, lsy, lip_h).cut(
      box(lx0 + lip_t, ly0 + lip_t, oh - lip_h - 1, lsx - 2 * lip_t, lsy - 2 * lip_t, lip_h + 2))
lid = lid.union(lip)
for y in (ly0, ly0 + lsy):             # snap bumps on the lip
    lid = lid.union(xbar(ox / 2 - snap_len / 2, y, oh - snap_z, snap_len, 2 * snap_r))
holder = zcyl(ring_x, cy, oh - lip_h, ring_od + 0.8 + 2 * 1.2, lip_h).cut(zcyl(ring_x, cy, oh - lip_h - 1, ring_od + 0.8, lip_h + 2))
lid = lid.union(holder).cut(zcyl(ring_x, cy, oh - 1, win_d, lid_t + 2))
lid_print = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, oy, oh + lid_t))

# ---- light cap, modelled in place on top of the lid ----
z0 = oh + lid_t
capb = box(ring_x - cap / 2, cy - cap / 2, z0, cap, cap, cap_h - spig_h).edges("|Z").fillet(3.0)
capb = capb.cut(box(ring_x - cap / 2 + cap_wall, cy - cap / 2 + cap_wall, z0 - 1, cap - 2 * cap_wall, cap - 2 * cap_wall, cap_h - spig_h - cap_top + 1))
spig = zcyl(ring_x, cy, z0 - spig_h, win_d - 0.4, spig_h + 0.01).cut(zcyl(ring_x, cy, z0 - spig_h - 1, win_d - 0.4 - 2 * spig_t, spig_h + 2))
frame = box(ring_x - cap / 2, cy - cap / 2, z0, cap, cap, 1.2).edges("|Z").fillet(3.0).cut(zcyl(ring_x, cy, z0 - 1, win_d - 0.4 - 2 * spig_t, 4))
capb = capb.union(frame).union(spig)   # bottom frame joins the walls to the spigot
cap_print = capb.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, 0))
bb = cap_print.val().BoundingBox()
cap_print = cap_print.translate((-bb.xmin, -bb.ymin, -bb.zmin))   # open side up, on the bed

P = ""   # write next to this script
for shape, name in ((base, "T6_caseA_base_v1"), (lid_print, "T6_caseA_lid_v1"), (cap_print, "T6_light_cap_v1")):
    cq.exporters.export(shape, P + name + ".stl", tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(shape, P + name + ".step")
cq.Assembly().add(base, name="base").add(lid, name="lid").add(capb, name="light_cap").save(P + "T6_caseA_assembly_v1.step")
for shape, name in ((base, "v3_base"), (lid, "v3_lid"), (capb, "v3_cap")):
    cq.exporters.export(shape, name + "_assembled.stl", tolerance=0.05, angularTolerance=0.2)
for s, n in ((base, "base"), (lid_print, "lid"), (cap_print, "cap")):
    b = s.val().BoundingBox()
    print("%s %.1f x %.1f x %.1f valid %s vol %.0f" % (n, b.xlen, b.ylen, b.zlen, s.val().isValid(), s.val().Volume()))
