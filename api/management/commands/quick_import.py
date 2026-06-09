import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import FuelStation


STATE_COORDS = {
    "AL": (32.8067, -86.7911), "AK": (61.3707, -152.4044), "AZ": (33.7298, -111.4312),
    "AR": (34.9697, -92.3731), "CA": (36.1162, -119.6816), "CO": (39.0598, -105.3111),
    "CT": (41.5978, -72.7554), "DE": (39.3185, -75.5071), "FL": (27.7663, -81.6868),
    "GA": (33.0406, -83.6431), "HI": (21.0943, -157.4983), "ID": (44.2998, -114.7420),
    "IL": (40.0417, -89.1965), "IN": (39.8494, -86.2583), "IA": (42.0115, -93.2105),
    "KS": (38.5266, -96.7265), "KY": (37.6681, -84.6701), "LA": (30.9735, -91.4299),
    "ME": (44.7002, -69.7187), "MD": (39.0639, -76.8021), "MA": (42.2371, -71.7084),
    "MI": (43.6124, -84.2400), "MN": (45.6759, -93.5797), "MS": (32.7459, -89.6786),
    "MO": (38.4624, -92.6103), "MT": (46.9219, -110.4544), "NE": (41.4925, -99.9018),
    "NV": (38.4199, -117.1219), "NH": (43.6684, -71.8018), "NJ": (40.0122, -74.3079),
    "NM": (34.0023, -106.4619), "NY": (42.1657, -74.9481), "NC": (35.6301, -79.8064),
    "ND": (47.5362, -99.7930), "OH": (40.3888, -82.7649), "OK": (35.5653, -96.9289),
    "OR": (44.5720, -122.0709), "PA": (40.5908, -77.2098), "RI": (41.6809, -71.5118),
    "SC": (33.8569, -80.9450), "SD": (44.2998, -99.4388), "TN": (35.7478, -86.6923),
    "TX": (31.0544, -97.5635), "UT": (40.1500, -111.8624), "VT": (44.0455, -72.7107),
    "VA": (37.7695, -78.1700), "WA": (47.4090, -120.5623), "WV": (38.7040, -80.6246),
    "WI": (44.5363, -89.8255), "WY": (42.7560, -107.3026), "DC": (38.8964, -77.0265),
}

IMPORTANT_CITIES = {
    ("Los Angeles", "CA"): (34.0522, -118.2437), ("New York", "NY"): (40.7128, -74.0060),
    ("Chicago", "IL"): (41.8781, -87.6298), ("Houston", "TX"): (29.7604, -95.3698),
    ("Phoenix", "AZ"): (33.4484, -112.0740), ("Philadelphia", "PA"): (39.9526, -75.1652),
    ("San Antonio", "TX"): (29.4241, -98.4936), ("San Diego", "CA"): (32.7157, -117.1611),
    ("Dallas", "TX"): (32.7767, -96.7970), ("San Jose", "CA"): (37.3382, -121.8863),
    ("Austin", "TX"): (30.2672, -97.7431), ("Jacksonville", "FL"): (30.3322, -81.6557),
    ("Fort Worth", "TX"): (32.7555, -97.3308), ("Columbus", "OH"): (39.9612, -82.9988),
    ("Charlotte", "NC"): (35.2271, -80.8431), ("Indianapolis", "IN"): (39.7684, -86.1581),
    ("San Francisco", "CA"): (37.7749, -122.4194), ("Seattle", "WA"): (47.6062, -122.3321),
    ("Denver", "CO"): (39.7392, -104.9903), ("Nashville", "TN"): (36.1627, -86.7816),
    ("Oklahoma City", "OK"): (35.4676, -97.5164), ("El Paso", "TX"): (31.7619, -106.4850),
    ("Washington", "DC"): (38.9072, -77.0369), ("Boston", "MA"): (42.3601, -71.0589),
    ("Las Vegas", "NV"): (36.1699, -115.1398), ("Portland", "OR"): (45.5152, -122.6784),
    ("Memphis", "TN"): (35.1495, -90.0490), ("Louisville", "KY"): (38.2527, -85.7585),
    ("Baltimore", "MD"): (39.2904, -76.6122), ("Milwaukee", "WI"): (43.0389, -87.9065),
    ("Albuquerque", "NM"): (35.0853, -106.6056), ("Tucson", "AZ"): (32.2226, -110.9747),
    ("Fresno", "CA"): (36.7378, -119.7871), ("Sacramento", "CA"): (38.5816, -121.4944),
    ("Mesa", "AZ"): (33.4152, -111.8315), ("Kansas City", "MO"): (39.0997, -94.5786),
    ("Atlanta", "GA"): (33.7490, -84.3880), ("Omaha", "NE"): (41.2565, -95.9345),
    ("Colorado Springs", "CO"): (38.8339, -104.8214), ("Raleigh", "NC"): (35.7796, -78.6382),
    ("Long Beach", "CA"): (33.7701, -118.1937), ("Virginia Beach", "VA"): (36.8529, -75.9780),
    ("Miami", "FL"): (25.7617, -80.1918), ("Oakland", "CA"): (37.8044, -122.2712),
    ("Minneapolis", "MN"): (44.9778, -93.2650), ("Tampa", "FL"): (27.9506, -82.4572),
    ("Tulsa", "OK"): (36.1537, -95.9945), ("Arlington", "TX"): (32.7357, -97.1081),
    ("New Orleans", "LA"): (29.9511, -90.0715), ("Cleveland", "OH"): (41.4993, -81.6944),
    ("Bakersfield", "CA"): (35.3733, -119.0187), ("Honolulu", "HI"): (21.3069, -157.8583),
    ("Anaheim", "CA"): (33.8366, -117.9143), ("Stockton", "CA"): (37.9577, -121.2908),
    ("Corpus Christi", "TX"): (27.8006, -97.3964), ("Riverside", "CA"): (33.9533, -117.3961),
    ("Santa Ana", "CA"): (33.7455, -117.8677), ("St. Louis", "MO"): (38.6270, -90.1994),
    ("Pittsburgh", "PA"): (40.4406, -79.9959), ("Cincinnati", "OH"): (39.1031, -84.5120),
}


class Command(BaseCommand):
    help = "Quick import with approximate city coordinates (no API calls)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV")

    def handle(self, *args, **options):
        FuelStation.objects.all().delete()

        rows = []
        with open(options["csv_path"], "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        unique_stations = {}
        for r in rows:
            key = (r["OPIS Truckstop ID"], r["Truckstop Name"].strip(), r["City"].strip(), r["State"].strip(), r["Address"].strip())
            if key not in unique_stations:
                unique_stations[key] = r

        bulk = []
        for r in unique_stations.values():
            city, state = r["City"].strip(), r["State"].strip()
            lat, lon = None, None

            if (city, state) in IMPORTANT_CITIES:
                lat, lon = IMPORTANT_CITIES[(city, state)]
            elif state in STATE_COORDS:
                import random
                base_lat, base_lon = STATE_COORDS[state]
                lat = base_lat + random.uniform(-1.5, 1.5)
                lon = base_lon + random.uniform(-1.5, 1.5)

            bulk.append(FuelStation(
                opis_truckstop_id=int(r["OPIS Truckstop ID"]),
                truckstop_name=r["Truckstop Name"].strip(),
                address=r["Address"].strip(),
                city=city,
                state=state,
                rack_id=int(r["Rack ID"]),
                retail_price=float(r["Retail Price"]),
                latitude=lat,
                longitude=lon,
            ))

        FuelStation.objects.bulk_create(bulk, ignore_conflicts=True)
        total = FuelStation.objects.count()
        with_coords = FuelStation.objects.filter(latitude__isnull=False).count()
        self.stdout.write(self.style.SUCCESS(
            f"Imported {total} stations ({with_coords} with approximate coordinates)"
        ))
