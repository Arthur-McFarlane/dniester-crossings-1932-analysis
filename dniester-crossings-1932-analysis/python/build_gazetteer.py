"""Gazetteer for the places named in persons.csv: coordinates, source, precision, and checks.
Run from the repository root:  python python/build_gazetteer.py   (writes data/gazetteer.csv)
Coordinates come from GeoNames, Wikipedia and Natural Earth, as stated for each place. The bank test
finds which side of the Dniester each place lies on, using the Natural Earth river line."""
import json, math
import pandas as pd

def dms(d, m, s=0): return round(d + m / 60 + s / 3600, 5)

GN, NE, WP = "GeoNames", "Natural Earth populated places (10m)", "Wikipedia"
# place_modern: (lat, lon, precision, source, note, check)
G = {
 # --- crossing places and origins along the Dniester
 "Cioburciu":      (46.685, 29.7475, "village", WP, "Chobruchi (Russian Чобручи), Slobozia district; checked October 2026", ""),
 "Hlinaia":        (46.64667, 29.80861, "village", WP, "Glinnoe (Russian Глиное), Slobozia district, next to Chobruchi and Korotnoe; not the Hlinaia of Grigoriopol district", ""),
 "Corotna":        (dms(46,37,59), dms(29,51,22), "village", GN, "", ""),
 "Speia":          (dms(46,58,58), dms(29,19,32), "village", GN, "left-bank record (GeoNames also lists a Speia 3 km NW labelled Anenii Noi)", ""),
 "Slobozia":       (dms(46,43,45), dms(29,42,16), "town",    GN, "Slobodzeia", ""),
 "Tirnauca":       (dms(46,48,44), dms(29,33,16), "village", GN, "Ternovka", ""),
 "Delacau":        (47.12806, 29.29944, "village", WP, "Delakeu (Russian Делакеу), Grigoriopol district", ""),
 "Molovata":       (47.33861, 29.09056, "village", WP, "Malovata of Dubossary raion (Soviet bank), today Molovata Nouă; old Molovata faces it across the river", ""),
 "Nezavertailovca":(dms(46,35,49), dms(29,56,15), "village", GN, "", ""),
 "Parcani":        (dms(46,51,3),  dms(29,30,54), "village", GN, "Parkany, between Tiraspol and Bendery", ""),
 "Caragas":        (dms(46,46,51), dms(29,40,58), "village", GN, "Karagash", ""),
 "Cocieri":        (47.30167, 29.1175, "village", GN, "Kuchery", ""),
 "Stroiesti":      (dms(47,53,22), dms(28,55,59), "village", GN, "Stroiintsy", ""),
 "Sucleia":        (dms(46,49,25), dms(29,39,52), "village", GN, "", ""),
 "Dorotcaia":      (dms(47,10,20), dms(29,12,12), "village", GN, "Dorotskoe", ""),
 "Podoima":        (47.99806, 28.77667, "village", WP, "Podoima commune, Camenca district", ""),
 "Beloci":         (dms(47,53,13), dms(28,58,41), "village", GN, "Beloch'", ""),
 "Telita":         (dms(46,57,25), dms(29,18,24), "village", GN, "Telitsa, on the Romanian bank; the crossing was by the island opposite it", ""),
 "Butor":          (47.042245, 29.405277, "village", GN, "", ""),
 "Jura":           (dms(47,31,3),  dms(29,2,33),  "village", GN, "Zhury", ""),
 "Rascova":        (dms(47,57,24), dms(28,49,26), "village", GN, "Rashkov", ""),
 "Popencu":        (47.599884, 29.006401, "village", GN, "Popenki", ""),
 "Hrusca":         (48.12222, 28.55111, "village", WP, "Grushka (Russian Грушка), Camenca district", ""),
 "Hyderym":        (47.71333, 28.97861, "village", WP, "Giderim, today Ghidirim (Russian Гидирим), Rîbnița district", ""),
 "Smalena":        (dms(47,45,29), dms(29,4,28),  "village", GN, "Shmalena", ""),
 "Roghi":          (dms(47,19,19), dms(29,8,23),  "village", GN, "Rogi", ""),
 "Pohreby":        (dms(47,10,52), dms(29,10,1),  "village", GN, "Pogreby, today Pohrebea", ""),
 "Goian":          (dms(47,22,40), dms(29,9,44),  "village", GN, "Goiany (left-bank record; another Goian lies near Chișinău)", ""),
 "Tabuleuca":      (47.404719, 29.106057, "village", GN, "Tsybulevka, today Ţîbuleuca", ""),
 "Teiu":           (dms(46,57,26), dms(29,23,47), "village", GN, "Teia", ""),
 "Mihailovca":     (dms(47,29,4),  dms(29,7,6),   "village", GN, "Mikhalevka (GeoNames variant); Rîbnița district", ""),
 "Yerzhovo":       (dms(47,48,17), dms(29,0,27),  "village", GN, "Erzhovo, today Hîrjău", ""),
 "Tocmagiu":       (46.944621, 29.378218, "village", GN, "Tokmadzhei (Tokmazeia)", ""),
 "Grigoriopol":    (47.15389, 29.3, "town", GN, "", ""),
 "Dubasari":       (47.26556, 29.16667, "town", GN, "Dubossary", ""),
 "Rybnitsa":       (47.76806, 29.01, "town", GN, "", ""),
 "Camenca":        (48.03222, 28.69889, "town", GN, "Kamenka", ""),
 "Tiraspol":       (46.8425, 29.62833, "town", GN, "", ""),
 "Bender":         (46.83139, 29.47667, "town", GN, "Bendery", ""),
 "Rezina":         (47.74833, 28.9675, "town", GN, "", ""),
 "Criuleni":       (47.21333, 29.15833, "town", GN, "Kriuliany", ""),
 "Chisinau":       (47.00889, 28.85917, "city", GN, "Kishinev", ""),
 "Balti":          (47.76278, 27.92833, "town", GN, "Bel'tsy", ""),
 # --- further afield
 "Balta":          (47.94, 29.62194, "town", WP, "", ""),
 "Shershentsi":    (dms(47,59,17), dms(29,0,31),  "village", GN, "Kodyma district", ""),
 "Zahnitkiv":      (dms(48,2,51),  dms(28,53,13), "village", GN, "Zagnitkovo; the one in Kodyma district (another lies 6 km NW in Vinnytsia oblast)", ""),
 "Hradenytsi":     (dms(46,35,48), dms(30,0,8),   "village", GN, "Gradenitsy, Odesa oblast", ""),
 "Voznesens'k":    (47.5504, 31.3333, "town", NE, "", ""),
 "Odesa":          (46.492, 30.7081, "city", NE, "", ""),
 "Uman":           (48.7543, 30.2109, "town", NE, "", ""),
 "Umans'kyi":      (48.7543, 30.2109, "district", NE, "Umanskii raion: placed at Uman, the district town", ""),
 "Khmelnytskyi":   (49.4249, 27.0015, "district", NE, "Proskurov okrug: placed at Proskurov (Khmelnytskyi), the okrug town", ""),
 "Sverdlovsk okrug":(56.852, 60.598, "district", NE, "placed at Sverdlovsk (Yekaterinburg), the okrug town", ""),
 "Chaplyginsky":   (53.233, 39.967, "district", WP, "Ranenburg raion: placed at Ranenburg (Chaplygin), the district town", ""),
 "Marx, Saratov":  (51.717, 46.75, "town", WP, "Marxstadt", ""),
 "Moscow":         (55.7541, 37.6136, "city", NE, "", ""),
 "Ufa":            (54.7919, 56.0381, "city", NE, "", ""),
 "Bucharest":      (44.4353, 26.098, "city", NE, "", ""),
 "Constanta":      (44.2027, 28.61, "city", NE, "", ""),
 "Mar'yanivka":    (None, None, "village", "", "Mar'ianovka of Grossulovo raion: GeoNames lists eight Mar'ianivkas in Odesa oblast and none can be matched to Grossulovo raion with confidence", "unresolved"),
 # --- not points
 "Kyiv":           (None, None, "region", "", "Ianishevka, Kiev oblast: village not identified; the modern name 'Kyiv' stands for the oblast", "unresolved"),
 "Bessarabia":     (None, None, "region", "", "a region, not a place", "region"),
 "Romania":        (None, None, "region", "", "a country, not a place", "region"),
 "Butuceni":       (47.52915, 29.02908, "village", GN, "Botushany, today Butuceni (Russian Бутучаны, formerly Ботушаны), Rîbnița district", ""),
 "Cainari":        (46.681963, 29.048334, "town", GN, "'Kainarskii uezd': Căinari, then in Romanian Bessarabia (Tighina county), today Căușeni district", ""),
}

P = pd.read_csv("data/persons.csv", dtype=str, keep_default_na=False)
used = set(P.location_modern) | set(P.origin_modern)
used.discard("unknown")
missing = used - set(G)
assert not missing, missing

# --- which bank? Signed side of the Dniester (Natural Earth 10m centreline), looking downstream.
rv = json.load(open("data/naturalearth/dniester.geojson"))
parts = []
for f in rv["features"]:
    if f["properties"].get("name") == "Dniester":
        g = f["geometry"]
        parts += g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
segs = []
for part in parts:
    for a, b in zip(part[:-1], part[1:]):
        segs.append((a, b))

def side(lat, lon):
    kx = math.cos(math.radians(lat)) * 111.32; ky = 110.57
    best = None
    for (x1, y1), (x2, y2) in segs:
        ax, ay = (x1 - lon) * kx, (y1 - lat) * ky
        bx, by = (x2 - lon) * kx, (y2 - lat) * ky
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy or 1)))
        px, py = ax + t * dx, ay + t * dy
        d = math.hypot(px, py)
        if best is None or d < best[0]:
            best = (d, dx, dy, -ax, -ay)
    d, dx, dy, ex, ey = best
    cross = dx * ey - dy * ex          # >0: point to the left of the segment direction
    return d, cross

# determine segment orientation: is the river drawn upstream->downstream?
first = [p for p in parts if len(p) > 50][0]
downstream_first = first[0][1] > first[-1][1]   # source is in the north-west, mouth in the south-east

rows = []
for name in sorted(used):
    lat, lon, prec, src, note, chk = G[name]
    bank, dist = "", ""
    if lat is not None and 46.0 < lat < 48.6 and 27.5 < lon < 30.6:
        d, cross = side(lat, lon)
        left = (cross > 0) == downstream_first
        bank = "left (Soviet)" if left else "right (Romanian)"
        dist = round(d, 1)
    rows.append(dict(place_modern=name, latitude=lat, longitude=lon, precision=prec, source=src,
                     bank_1932=bank, km_from_river_line=dist, note=note, status=chk or "ok",
                     n_as_crossing_place=int((P.location_modern == name).sum()),
                     n_as_origin=int((P.origin_modern == name).sum())))
T = pd.DataFrame(rows)
T.to_csv("data/gazetteer.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100); pd.set_option("display.max_colwidth", 40)
print(T[["place_modern", "latitude", "longitude", "precision", "bank_1932", "km_from_river_line", "status", "n_as_crossing_place", "n_as_origin"]].to_string(index=False))
