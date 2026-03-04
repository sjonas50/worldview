"""Seed Location nodes for the OSINT knowledge graph.

Sources:
- Military bases: BUILD_DOCUMENT.md + additional strategic bases
- Strategic chokepoints: BUILD_DOCUMENT.md + additional waterways
- Airports: converted from src/data/airports.ts (~280 airports)
"""

import logging

logger = logging.getLogger("worldview-ingestion")

MILITARY_BASES = [
    {"id": "base-al-udeid", "name": "Al Udeid Air Base", "type": "base", "lat": 25.1174, "lon": 51.3150, "country": "QA"},
    {"id": "base-al-dhafra", "name": "Al Dhafra Air Base", "type": "base", "lat": 24.2483, "lon": 54.5477, "country": "AE"},
    {"id": "base-diego-garcia", "name": "Diego Garcia", "type": "base", "lat": -7.3133, "lon": 72.4111, "country": "US"},
    {"id": "base-incirlik", "name": "Incirlik Air Base", "type": "base", "lat": 37.0021, "lon": 35.4259, "country": "TR"},
    {"id": "base-ramstein", "name": "Ramstein Air Base", "type": "base", "lat": 49.4369, "lon": 7.6003, "country": "DE"},
    {"id": "base-aviano", "name": "Aviano Air Base", "type": "base", "lat": 46.0319, "lon": 12.5965, "country": "IT"},
    {"id": "base-kadena", "name": "Kadena Air Base", "type": "base", "lat": 26.3516, "lon": 127.7669, "country": "JP"},
    {"id": "base-osan", "name": "Osan Air Base", "type": "base", "lat": 37.0908, "lon": 127.0297, "country": "KR"},
    {"id": "base-andersen", "name": "Andersen Air Force Base", "type": "base", "lat": 13.5840, "lon": 144.9243, "country": "GU"},
    {"id": "base-lemonnier", "name": "Camp Lemonnier", "type": "base", "lat": 11.5471, "lon": 43.1594, "country": "DJ"},
    {"id": "base-thule", "name": "Thule Air Base", "type": "base", "lat": 76.5312, "lon": -68.7032, "country": "GL"},
    {"id": "base-lakenheath", "name": "RAF Lakenheath", "type": "base", "lat": 52.4093, "lon": 0.5609, "country": "GB"},
    {"id": "base-mildenhall", "name": "RAF Mildenhall", "type": "base", "lat": 52.3612, "lon": 0.4864, "country": "GB"},
    {"id": "base-yokota", "name": "Yokota Air Base", "type": "base", "lat": 35.7485, "lon": 139.3487, "country": "JP"},
    {"id": "base-misawa", "name": "Misawa Air Base", "type": "base", "lat": 40.7032, "lon": 141.3686, "country": "JP"},
    {"id": "base-rota", "name": "Naval Station Rota", "type": "base", "lat": 36.6452, "lon": -6.3495, "country": "ES"},
    {"id": "base-sigonella", "name": "NAS Sigonella", "type": "base", "lat": 37.4017, "lon": 14.9222, "country": "IT"},
    {"id": "base-bahrain", "name": "NSA Bahrain", "type": "base", "lat": 26.2308, "lon": 50.6516, "country": "BH"},
]

STRATEGIC_CHOKEPOINTS = [
    {"id": "strait-hormuz", "name": "Strait of Hormuz", "type": "strait", "lat": 26.5667, "lon": 56.2500, "country": "IR/OM"},
    {"id": "strait-bab-el-mandeb", "name": "Bab el-Mandeb", "type": "strait", "lat": 12.5833, "lon": 43.3333, "country": "YE/DJ"},
    {"id": "strait-malacca", "name": "Strait of Malacca", "type": "strait", "lat": 2.5000, "lon": 101.0000, "country": "MY/ID"},
    {"id": "strait-gibraltar", "name": "Strait of Gibraltar", "type": "strait", "lat": 35.9667, "lon": -5.5000, "country": "ES/MA"},
    {"id": "strait-taiwan", "name": "Taiwan Strait", "type": "strait", "lat": 24.0000, "lon": 119.5000, "country": "TW/CN"},
    {"id": "strait-bosphorus", "name": "Bosphorus Strait", "type": "strait", "lat": 41.1190, "lon": 29.0753, "country": "TR"},
    {"id": "canal-suez", "name": "Suez Canal", "type": "strait", "lat": 30.4578, "lon": 32.3498, "country": "EG"},
    {"id": "canal-panama", "name": "Panama Canal", "type": "strait", "lat": 9.0800, "lon": -79.6800, "country": "PA"},
    {"id": "strait-danish", "name": "Danish Straits", "type": "strait", "lat": 55.6500, "lon": 12.6000, "country": "DK"},
    {"id": "gap-giuk", "name": "GIUK Gap", "type": "strait", "lat": 63.0000, "lon": -15.0000, "country": "IS/GB"},
    {"id": "strait-korea", "name": "Korea Strait", "type": "strait", "lat": 34.0000, "lon": 129.0000, "country": "KR/JP"},
    {"id": "strait-mozambique", "name": "Mozambique Channel", "type": "strait", "lat": -17.0000, "lon": 41.0000, "country": "MZ/MG"},
]

# Converted from src/data/airports.ts
AIRPORTS = [
    # North America
    {"id": "airport-atl", "iata": "ATL", "name": "Atlanta", "type": "airport", "lat": 33.6407, "lon": -84.4277, "country": "US"},
    {"id": "airport-ord", "iata": "ORD", "name": "Chicago O'Hare", "type": "airport", "lat": 41.9742, "lon": -87.9073, "country": "US"},
    {"id": "airport-dfw", "iata": "DFW", "name": "Dallas/Fort Worth", "type": "airport", "lat": 32.8998, "lon": -97.0403, "country": "US"},
    {"id": "airport-den", "iata": "DEN", "name": "Denver", "type": "airport", "lat": 39.8561, "lon": -104.6737, "country": "US"},
    {"id": "airport-lax", "iata": "LAX", "name": "Los Angeles", "type": "airport", "lat": 33.9425, "lon": -118.4081, "country": "US"},
    {"id": "airport-jfk", "iata": "JFK", "name": "New York JFK", "type": "airport", "lat": 40.6413, "lon": -73.7781, "country": "US"},
    {"id": "airport-sfo", "iata": "SFO", "name": "San Francisco", "type": "airport", "lat": 37.6213, "lon": -122.3790, "country": "US"},
    {"id": "airport-sea", "iata": "SEA", "name": "Seattle", "type": "airport", "lat": 47.4502, "lon": -122.3088, "country": "US"},
    {"id": "airport-las", "iata": "LAS", "name": "Las Vegas", "type": "airport", "lat": 36.0840, "lon": -115.1537, "country": "US"},
    {"id": "airport-mco", "iata": "MCO", "name": "Orlando", "type": "airport", "lat": 28.4312, "lon": -81.3081, "country": "US"},
    {"id": "airport-clt", "iata": "CLT", "name": "Charlotte", "type": "airport", "lat": 35.2144, "lon": -80.9473, "country": "US"},
    {"id": "airport-mia", "iata": "MIA", "name": "Miami", "type": "airport", "lat": 25.7959, "lon": -80.2870, "country": "US"},
    {"id": "airport-phx", "iata": "PHX", "name": "Phoenix", "type": "airport", "lat": 33.4373, "lon": -112.0078, "country": "US"},
    {"id": "airport-ewr", "iata": "EWR", "name": "Newark", "type": "airport", "lat": 40.6895, "lon": -74.1745, "country": "US"},
    {"id": "airport-msp", "iata": "MSP", "name": "Minneapolis", "type": "airport", "lat": 44.8848, "lon": -93.2223, "country": "US"},
    {"id": "airport-dtw", "iata": "DTW", "name": "Detroit", "type": "airport", "lat": 42.2124, "lon": -83.3534, "country": "US"},
    {"id": "airport-bos", "iata": "BOS", "name": "Boston", "type": "airport", "lat": 42.3656, "lon": -71.0096, "country": "US"},
    {"id": "airport-fll", "iata": "FLL", "name": "Fort Lauderdale", "type": "airport", "lat": 26.0742, "lon": -80.1506, "country": "US"},
    {"id": "airport-iah", "iata": "IAH", "name": "Houston Intercontinental", "type": "airport", "lat": 29.9902, "lon": -95.3368, "country": "US"},
    {"id": "airport-bwi", "iata": "BWI", "name": "Baltimore", "type": "airport", "lat": 39.1754, "lon": -76.6683, "country": "US"},
    {"id": "airport-slc", "iata": "SLC", "name": "Salt Lake City", "type": "airport", "lat": 40.7899, "lon": -111.9791, "country": "US"},
    {"id": "airport-dca", "iata": "DCA", "name": "Washington Reagan", "type": "airport", "lat": 38.8512, "lon": -77.0402, "country": "US"},
    {"id": "airport-iad", "iata": "IAD", "name": "Washington Dulles", "type": "airport", "lat": 38.9531, "lon": -77.4565, "country": "US"},
    {"id": "airport-san", "iata": "SAN", "name": "San Diego", "type": "airport", "lat": 32.7338, "lon": -117.1933, "country": "US"},
    {"id": "airport-tpa", "iata": "TPA", "name": "Tampa", "type": "airport", "lat": 27.9756, "lon": -82.5333, "country": "US"},
    {"id": "airport-pdx", "iata": "PDX", "name": "Portland", "type": "airport", "lat": 45.5898, "lon": -122.5951, "country": "US"},
    {"id": "airport-hnl", "iata": "HNL", "name": "Honolulu", "type": "airport", "lat": 21.3187, "lon": -157.9224, "country": "US"},
    {"id": "airport-stl", "iata": "STL", "name": "St Louis", "type": "airport", "lat": 38.7487, "lon": -90.3700, "country": "US"},
    {"id": "airport-bna", "iata": "BNA", "name": "Nashville", "type": "airport", "lat": 36.1263, "lon": -86.6774, "country": "US"},
    {"id": "airport-aus", "iata": "AUS", "name": "Austin", "type": "airport", "lat": 30.1975, "lon": -97.6664, "country": "US"},
    {"id": "airport-rdu", "iata": "RDU", "name": "Raleigh-Durham", "type": "airport", "lat": 35.8776, "lon": -78.7875, "country": "US"},
    {"id": "airport-mci", "iata": "MCI", "name": "Kansas City", "type": "airport", "lat": 39.2976, "lon": -94.7139, "country": "US"},
    {"id": "airport-hou", "iata": "HOU", "name": "Houston Hobby", "type": "airport", "lat": 29.6454, "lon": -95.2789, "country": "US"},
    {"id": "airport-msy", "iata": "MSY", "name": "New Orleans", "type": "airport", "lat": 29.9934, "lon": -90.2580, "country": "US"},
    {"id": "airport-smf", "iata": "SMF", "name": "Sacramento", "type": "airport", "lat": 38.6954, "lon": -121.5908, "country": "US"},
    {"id": "airport-pit", "iata": "PIT", "name": "Pittsburgh", "type": "airport", "lat": 40.4915, "lon": -80.2329, "country": "US"},
    {"id": "airport-cle", "iata": "CLE", "name": "Cleveland", "type": "airport", "lat": 41.4058, "lon": -81.8540, "country": "US"},
    {"id": "airport-ind", "iata": "IND", "name": "Indianapolis", "type": "airport", "lat": 39.7173, "lon": -86.2944, "country": "US"},
    {"id": "airport-cmh", "iata": "CMH", "name": "Columbus", "type": "airport", "lat": 39.9980, "lon": -82.8919, "country": "US"},
    {"id": "airport-oak", "iata": "OAK", "name": "Oakland", "type": "airport", "lat": 37.7213, "lon": -122.2208, "country": "US"},
    {"id": "airport-sjc", "iata": "SJC", "name": "San Jose", "type": "airport", "lat": 37.3626, "lon": -121.9290, "country": "US"},
    {"id": "airport-rsw", "iata": "RSW", "name": "Fort Myers", "type": "airport", "lat": 26.5362, "lon": -81.7552, "country": "US"},
    {"id": "airport-sat", "iata": "SAT", "name": "San Antonio", "type": "airport", "lat": 29.5337, "lon": -98.4698, "country": "US"},
    {"id": "airport-pbi", "iata": "PBI", "name": "West Palm Beach", "type": "airport", "lat": 26.6832, "lon": -80.0956, "country": "US"},
    {"id": "airport-mke", "iata": "MKE", "name": "Milwaukee", "type": "airport", "lat": 42.9472, "lon": -87.8966, "country": "US"},
    {"id": "airport-jax", "iata": "JAX", "name": "Jacksonville", "type": "airport", "lat": 30.4941, "lon": -81.6879, "country": "US"},
    {"id": "airport-anc", "iata": "ANC", "name": "Anchorage", "type": "airport", "lat": 61.1743, "lon": -149.9963, "country": "US"},
    {"id": "airport-abq", "iata": "ABQ", "name": "Albuquerque", "type": "airport", "lat": 35.0402, "lon": -106.6094, "country": "US"},
    {"id": "airport-oma", "iata": "OMA", "name": "Omaha", "type": "airport", "lat": 41.3032, "lon": -95.8941, "country": "US"},
    {"id": "airport-buf", "iata": "BUF", "name": "Buffalo", "type": "airport", "lat": 42.9405, "lon": -78.7322, "country": "US"},
    {"id": "airport-ont", "iata": "ONT", "name": "Ontario CA", "type": "airport", "lat": 34.0560, "lon": -117.6012, "country": "US"},
    {"id": "airport-bur", "iata": "BUR", "name": "Burbank", "type": "airport", "lat": 34.1975, "lon": -118.3586, "country": "US"},
    {"id": "airport-pvd", "iata": "PVD", "name": "Providence", "type": "airport", "lat": 41.7246, "lon": -71.4282, "country": "US"},
    {"id": "airport-ric", "iata": "RIC", "name": "Richmond", "type": "airport", "lat": 37.5052, "lon": -77.3197, "country": "US"},
    {"id": "airport-okc", "iata": "OKC", "name": "Oklahoma City", "type": "airport", "lat": 35.3931, "lon": -97.6007, "country": "US"},
    {"id": "airport-mem", "iata": "MEM", "name": "Memphis", "type": "airport", "lat": 35.0424, "lon": -89.9767, "country": "US"},
    {"id": "airport-cvg", "iata": "CVG", "name": "Cincinnati", "type": "airport", "lat": 39.0488, "lon": -84.6678, "country": "US"},
    {"id": "airport-lga", "iata": "LGA", "name": "New York LaGuardia", "type": "airport", "lat": 40.7769, "lon": -73.8740, "country": "US"},
    # Canada
    {"id": "airport-yyz", "iata": "YYZ", "name": "Toronto Pearson", "type": "airport", "lat": 43.6777, "lon": -79.6248, "country": "CA"},
    {"id": "airport-yvr", "iata": "YVR", "name": "Vancouver", "type": "airport", "lat": 49.1947, "lon": -123.1792, "country": "CA"},
    {"id": "airport-yul", "iata": "YUL", "name": "Montreal", "type": "airport", "lat": 45.4706, "lon": -73.7408, "country": "CA"},
    {"id": "airport-yyc", "iata": "YYC", "name": "Calgary", "type": "airport", "lat": 51.1215, "lon": -114.0076, "country": "CA"},
    {"id": "airport-yeg", "iata": "YEG", "name": "Edmonton", "type": "airport", "lat": 53.3097, "lon": -113.5800, "country": "CA"},
    {"id": "airport-yow", "iata": "YOW", "name": "Ottawa", "type": "airport", "lat": 45.3225, "lon": -75.6692, "country": "CA"},
    {"id": "airport-ywg", "iata": "YWG", "name": "Winnipeg", "type": "airport", "lat": 49.9100, "lon": -97.2399, "country": "CA"},
    {"id": "airport-yhz", "iata": "YHZ", "name": "Halifax", "type": "airport", "lat": 44.8808, "lon": -63.5086, "country": "CA"},
    # Mexico
    {"id": "airport-mex", "iata": "MEX", "name": "Mexico City", "type": "airport", "lat": 19.4363, "lon": -99.0721, "country": "MX"},
    {"id": "airport-cun", "iata": "CUN", "name": "Cancun", "type": "airport", "lat": 21.0365, "lon": -86.8771, "country": "MX"},
    {"id": "airport-gdl", "iata": "GDL", "name": "Guadalajara", "type": "airport", "lat": 20.5218, "lon": -103.3114, "country": "MX"},
    {"id": "airport-mty", "iata": "MTY", "name": "Monterrey", "type": "airport", "lat": 25.7785, "lon": -100.1068, "country": "MX"},
    {"id": "airport-sjd", "iata": "SJD", "name": "San Jose del Cabo", "type": "airport", "lat": 23.1518, "lon": -109.7215, "country": "MX"},
    {"id": "airport-pvr", "iata": "PVR", "name": "Puerto Vallarta", "type": "airport", "lat": 20.6801, "lon": -105.2544, "country": "MX"},
    # Europe
    {"id": "airport-lhr", "iata": "LHR", "name": "London Heathrow", "type": "airport", "lat": 51.4700, "lon": -0.4543, "country": "GB"},
    {"id": "airport-lgw", "iata": "LGW", "name": "London Gatwick", "type": "airport", "lat": 51.1537, "lon": -0.1821, "country": "GB"},
    {"id": "airport-stn", "iata": "STN", "name": "London Stansted", "type": "airport", "lat": 51.8860, "lon": 0.2389, "country": "GB"},
    {"id": "airport-ltn", "iata": "LTN", "name": "London Luton", "type": "airport", "lat": 51.8747, "lon": -0.3684, "country": "GB"},
    {"id": "airport-man", "iata": "MAN", "name": "Manchester", "type": "airport", "lat": 53.3537, "lon": -2.2750, "country": "GB"},
    {"id": "airport-edi", "iata": "EDI", "name": "Edinburgh", "type": "airport", "lat": 55.9508, "lon": -3.3726, "country": "GB"},
    {"id": "airport-bhx", "iata": "BHX", "name": "Birmingham UK", "type": "airport", "lat": 52.4539, "lon": -1.7480, "country": "GB"},
    {"id": "airport-brs", "iata": "BRS", "name": "Bristol", "type": "airport", "lat": 51.3827, "lon": -2.7191, "country": "GB"},
    {"id": "airport-gla", "iata": "GLA", "name": "Glasgow", "type": "airport", "lat": 55.8642, "lon": -4.4331, "country": "GB"},
    {"id": "airport-cdg", "iata": "CDG", "name": "Paris CDG", "type": "airport", "lat": 49.0097, "lon": 2.5479, "country": "FR"},
    {"id": "airport-ory", "iata": "ORY", "name": "Paris Orly", "type": "airport", "lat": 48.7233, "lon": 2.3794, "country": "FR"},
    {"id": "airport-ams", "iata": "AMS", "name": "Amsterdam", "type": "airport", "lat": 52.3105, "lon": 4.7683, "country": "NL"},
    {"id": "airport-fra", "iata": "FRA", "name": "Frankfurt", "type": "airport", "lat": 50.0379, "lon": 8.5622, "country": "DE"},
    {"id": "airport-muc", "iata": "MUC", "name": "Munich", "type": "airport", "lat": 48.3537, "lon": 11.7750, "country": "DE"},
    {"id": "airport-dus", "iata": "DUS", "name": "Dusseldorf", "type": "airport", "lat": 51.2896, "lon": 6.7668, "country": "DE"},
    {"id": "airport-ber", "iata": "BER", "name": "Berlin", "type": "airport", "lat": 52.3667, "lon": 13.5033, "country": "DE"},
    {"id": "airport-ham", "iata": "HAM", "name": "Hamburg", "type": "airport", "lat": 53.6304, "lon": 10.0065, "country": "DE"},
    {"id": "airport-cgn", "iata": "CGN", "name": "Cologne", "type": "airport", "lat": 50.8659, "lon": 7.1427, "country": "DE"},
    {"id": "airport-str", "iata": "STR", "name": "Stuttgart", "type": "airport", "lat": 48.6899, "lon": 9.2220, "country": "DE"},
    {"id": "airport-mad", "iata": "MAD", "name": "Madrid", "type": "airport", "lat": 40.4983, "lon": -3.5676, "country": "ES"},
    {"id": "airport-bcn", "iata": "BCN", "name": "Barcelona", "type": "airport", "lat": 41.2974, "lon": 2.0785, "country": "ES"},
    {"id": "airport-pmi", "iata": "PMI", "name": "Palma de Mallorca", "type": "airport", "lat": 39.5517, "lon": 2.7388, "country": "ES"},
    {"id": "airport-agp", "iata": "AGP", "name": "Malaga", "type": "airport", "lat": 36.6749, "lon": -4.4991, "country": "ES"},
    {"id": "airport-alc", "iata": "ALC", "name": "Alicante", "type": "airport", "lat": 38.2822, "lon": -0.5582, "country": "ES"},
    {"id": "airport-fco", "iata": "FCO", "name": "Rome Fiumicino", "type": "airport", "lat": 41.8003, "lon": 12.2389, "country": "IT"},
    {"id": "airport-mxp", "iata": "MXP", "name": "Milan Malpensa", "type": "airport", "lat": 45.6306, "lon": 8.7281, "country": "IT"},
    {"id": "airport-lin", "iata": "LIN", "name": "Milan Linate", "type": "airport", "lat": 45.4505, "lon": 9.2764, "country": "IT"},
    {"id": "airport-vce", "iata": "VCE", "name": "Venice", "type": "airport", "lat": 45.5053, "lon": 12.3519, "country": "IT"},
    {"id": "airport-nap", "iata": "NAP", "name": "Naples", "type": "airport", "lat": 40.8860, "lon": 14.2908, "country": "IT"},
    {"id": "airport-ist", "iata": "IST", "name": "Istanbul", "type": "airport", "lat": 41.2753, "lon": 28.7519, "country": "TR"},
    {"id": "airport-saw", "iata": "SAW", "name": "Istanbul Sabiha", "type": "airport", "lat": 40.8986, "lon": 29.3092, "country": "TR"},
    {"id": "airport-ayt", "iata": "AYT", "name": "Antalya", "type": "airport", "lat": 36.8987, "lon": 30.8005, "country": "TR"},
    {"id": "airport-esb", "iata": "ESB", "name": "Ankara", "type": "airport", "lat": 40.1281, "lon": 32.9951, "country": "TR"},
    {"id": "airport-ath", "iata": "ATH", "name": "Athens", "type": "airport", "lat": 37.9364, "lon": 23.9445, "country": "GR"},
    {"id": "airport-zrh", "iata": "ZRH", "name": "Zurich", "type": "airport", "lat": 47.4647, "lon": 8.5492, "country": "CH"},
    {"id": "airport-gva", "iata": "GVA", "name": "Geneva", "type": "airport", "lat": 46.2381, "lon": 6.1089, "country": "CH"},
    {"id": "airport-vie", "iata": "VIE", "name": "Vienna", "type": "airport", "lat": 48.1103, "lon": 16.5697, "country": "AT"},
    {"id": "airport-bru", "iata": "BRU", "name": "Brussels", "type": "airport", "lat": 50.9014, "lon": 4.4844, "country": "BE"},
    {"id": "airport-lis", "iata": "LIS", "name": "Lisbon", "type": "airport", "lat": 38.7756, "lon": -9.1354, "country": "PT"},
    {"id": "airport-opo", "iata": "OPO", "name": "Porto", "type": "airport", "lat": 41.2481, "lon": -8.6814, "country": "PT"},
    {"id": "airport-cph", "iata": "CPH", "name": "Copenhagen", "type": "airport", "lat": 55.6180, "lon": 12.6561, "country": "DK"},
    {"id": "airport-osl", "iata": "OSL", "name": "Oslo", "type": "airport", "lat": 60.1976, "lon": 11.1004, "country": "NO"},
    {"id": "airport-arn", "iata": "ARN", "name": "Stockholm Arlanda", "type": "airport", "lat": 59.6498, "lon": 17.9238, "country": "SE"},
    {"id": "airport-hel", "iata": "HEL", "name": "Helsinki", "type": "airport", "lat": 60.3172, "lon": 24.9633, "country": "FI"},
    {"id": "airport-waw", "iata": "WAW", "name": "Warsaw", "type": "airport", "lat": 52.1657, "lon": 20.9671, "country": "PL"},
    {"id": "airport-prg", "iata": "PRG", "name": "Prague", "type": "airport", "lat": 50.1008, "lon": 14.2600, "country": "CZ"},
    {"id": "airport-bud", "iata": "BUD", "name": "Budapest", "type": "airport", "lat": 47.4369, "lon": 19.2556, "country": "HU"},
    {"id": "airport-otp", "iata": "OTP", "name": "Bucharest", "type": "airport", "lat": 44.5711, "lon": 26.0850, "country": "RO"},
    {"id": "airport-sof", "iata": "SOF", "name": "Sofia", "type": "airport", "lat": 42.6952, "lon": 23.4062, "country": "BG"},
    {"id": "airport-beg", "iata": "BEG", "name": "Belgrade", "type": "airport", "lat": 44.8184, "lon": 20.3091, "country": "RS"},
    {"id": "airport-zag", "iata": "ZAG", "name": "Zagreb", "type": "airport", "lat": 45.7429, "lon": 16.0688, "country": "HR"},
    {"id": "airport-dub", "iata": "DUB", "name": "Dublin", "type": "airport", "lat": 53.4264, "lon": -6.2499, "country": "IE"},
    {"id": "airport-snn", "iata": "SNN", "name": "Shannon", "type": "airport", "lat": 52.7020, "lon": -8.9249, "country": "IE"},
    {"id": "airport-kef", "iata": "KEF", "name": "Reykjavik Keflavik", "type": "airport", "lat": 63.9850, "lon": -22.6056, "country": "IS"},
    {"id": "airport-tfs", "iata": "TFS", "name": "Tenerife South", "type": "airport", "lat": 28.0445, "lon": -16.5725, "country": "ES"},
    {"id": "airport-lpa", "iata": "LPA", "name": "Gran Canaria", "type": "airport", "lat": 27.9319, "lon": -15.3866, "country": "ES"},
    {"id": "airport-nce", "iata": "NCE", "name": "Nice", "type": "airport", "lat": 43.6584, "lon": 7.2159, "country": "FR"},
    {"id": "airport-mrs", "iata": "MRS", "name": "Marseille", "type": "airport", "lat": 43.4393, "lon": 5.2214, "country": "FR"},
    {"id": "airport-lys", "iata": "LYS", "name": "Lyon", "type": "airport", "lat": 45.7256, "lon": 5.0811, "country": "FR"},
    {"id": "airport-tls", "iata": "TLS", "name": "Toulouse", "type": "airport", "lat": 43.6291, "lon": 1.3638, "country": "FR"},
    {"id": "airport-bod", "iata": "BOD", "name": "Bordeaux", "type": "airport", "lat": 44.8283, "lon": -0.7157, "country": "FR"},
    # Middle East
    {"id": "airport-dxb", "iata": "DXB", "name": "Dubai", "type": "airport", "lat": 25.2532, "lon": 55.3657, "country": "AE"},
    {"id": "airport-auh", "iata": "AUH", "name": "Abu Dhabi", "type": "airport", "lat": 24.4330, "lon": 54.6511, "country": "AE"},
    {"id": "airport-doh", "iata": "DOH", "name": "Doha", "type": "airport", "lat": 25.2731, "lon": 51.6081, "country": "QA"},
    {"id": "airport-ruh", "iata": "RUH", "name": "Riyadh", "type": "airport", "lat": 24.9576, "lon": 46.6988, "country": "SA"},
    {"id": "airport-jed", "iata": "JED", "name": "Jeddah", "type": "airport", "lat": 21.6796, "lon": 39.1565, "country": "SA"},
    {"id": "airport-bah", "iata": "BAH", "name": "Bahrain", "type": "airport", "lat": 26.2708, "lon": 50.6336, "country": "BH"},
    {"id": "airport-kwi", "iata": "KWI", "name": "Kuwait", "type": "airport", "lat": 29.2266, "lon": 47.9689, "country": "KW"},
    {"id": "airport-mct", "iata": "MCT", "name": "Muscat", "type": "airport", "lat": 23.5933, "lon": 58.2844, "country": "OM"},
    {"id": "airport-amm", "iata": "AMM", "name": "Amman", "type": "airport", "lat": 31.7226, "lon": 35.9932, "country": "JO"},
    {"id": "airport-bey", "iata": "BEY", "name": "Beirut", "type": "airport", "lat": 33.8209, "lon": 35.4884, "country": "LB"},
    {"id": "airport-tlv", "iata": "TLV", "name": "Tel Aviv", "type": "airport", "lat": 32.0055, "lon": 34.8854, "country": "IL"},
    {"id": "airport-cai", "iata": "CAI", "name": "Cairo", "type": "airport", "lat": 30.1219, "lon": 31.4056, "country": "EG"},
    {"id": "airport-hrg", "iata": "HRG", "name": "Hurghada", "type": "airport", "lat": 27.1783, "lon": 33.7994, "country": "EG"},
    {"id": "airport-ssh", "iata": "SSH", "name": "Sharm El Sheikh", "type": "airport", "lat": 27.9773, "lon": 34.3945, "country": "EG"},
    {"id": "airport-ika", "iata": "IKA", "name": "Tehran Imam Khomeini", "type": "airport", "lat": 35.4161, "lon": 51.1522, "country": "IR"},
    # Asia-Pacific
    {"id": "airport-hnd", "iata": "HND", "name": "Tokyo Haneda", "type": "airport", "lat": 35.5494, "lon": 139.7798, "country": "JP"},
    {"id": "airport-nrt", "iata": "NRT", "name": "Tokyo Narita", "type": "airport", "lat": 35.7720, "lon": 140.3929, "country": "JP"},
    {"id": "airport-kix", "iata": "KIX", "name": "Osaka Kansai", "type": "airport", "lat": 34.4347, "lon": 135.2441, "country": "JP"},
    {"id": "airport-icn", "iata": "ICN", "name": "Seoul Incheon", "type": "airport", "lat": 37.4602, "lon": 126.4407, "country": "KR"},
    {"id": "airport-gmp", "iata": "GMP", "name": "Seoul Gimpo", "type": "airport", "lat": 37.5583, "lon": 126.7906, "country": "KR"},
    {"id": "airport-pek", "iata": "PEK", "name": "Beijing Capital", "type": "airport", "lat": 40.0799, "lon": 116.6031, "country": "CN"},
    {"id": "airport-pkx", "iata": "PKX", "name": "Beijing Daxing", "type": "airport", "lat": 39.5098, "lon": 116.4105, "country": "CN"},
    {"id": "airport-pvg", "iata": "PVG", "name": "Shanghai Pudong", "type": "airport", "lat": 31.1443, "lon": 121.8083, "country": "CN"},
    {"id": "airport-sha", "iata": "SHA", "name": "Shanghai Hongqiao", "type": "airport", "lat": 31.1979, "lon": 121.3363, "country": "CN"},
    {"id": "airport-can", "iata": "CAN", "name": "Guangzhou", "type": "airport", "lat": 23.3924, "lon": 113.2988, "country": "CN"},
    {"id": "airport-hkg", "iata": "HKG", "name": "Hong Kong", "type": "airport", "lat": 22.3080, "lon": 113.9185, "country": "HK"},
    {"id": "airport-sin", "iata": "SIN", "name": "Singapore Changi", "type": "airport", "lat": 1.3644, "lon": 103.9915, "country": "SG"},
    {"id": "airport-bkk", "iata": "BKK", "name": "Bangkok Suvarnabhumi", "type": "airport", "lat": 13.6900, "lon": 100.7501, "country": "TH"},
    {"id": "airport-dmk", "iata": "DMK", "name": "Bangkok Don Mueang", "type": "airport", "lat": 13.9126, "lon": 100.6068, "country": "TH"},
    {"id": "airport-kul", "iata": "KUL", "name": "Kuala Lumpur", "type": "airport", "lat": 2.7456, "lon": 101.7099, "country": "MY"},
    {"id": "airport-cgk", "iata": "CGK", "name": "Jakarta", "type": "airport", "lat": -6.1256, "lon": 106.6559, "country": "ID"},
    {"id": "airport-mnl", "iata": "MNL", "name": "Manila", "type": "airport", "lat": 14.5086, "lon": 121.0198, "country": "PH"},
    {"id": "airport-sgn", "iata": "SGN", "name": "Ho Chi Minh City", "type": "airport", "lat": 10.8188, "lon": 106.6520, "country": "VN"},
    {"id": "airport-han", "iata": "HAN", "name": "Hanoi", "type": "airport", "lat": 21.2187, "lon": 105.8042, "country": "VN"},
    {"id": "airport-del", "iata": "DEL", "name": "New Delhi", "type": "airport", "lat": 28.5562, "lon": 77.1000, "country": "IN"},
    {"id": "airport-bom", "iata": "BOM", "name": "Mumbai", "type": "airport", "lat": 19.0896, "lon": 72.8656, "country": "IN"},
    {"id": "airport-blr", "iata": "BLR", "name": "Bangalore", "type": "airport", "lat": 13.1986, "lon": 77.7066, "country": "IN"},
    {"id": "airport-maa", "iata": "MAA", "name": "Chennai", "type": "airport", "lat": 12.9941, "lon": 80.1709, "country": "IN"},
    {"id": "airport-hyd", "iata": "HYD", "name": "Hyderabad", "type": "airport", "lat": 17.2403, "lon": 78.4294, "country": "IN"},
    {"id": "airport-ccu", "iata": "CCU", "name": "Kolkata", "type": "airport", "lat": 22.6520, "lon": 88.4463, "country": "IN"},
    {"id": "airport-cok", "iata": "COK", "name": "Kochi", "type": "airport", "lat": 10.1520, "lon": 76.4019, "country": "IN"},
    {"id": "airport-cmb", "iata": "CMB", "name": "Colombo", "type": "airport", "lat": 7.1808, "lon": 79.8841, "country": "LK"},
    {"id": "airport-dac", "iata": "DAC", "name": "Dhaka", "type": "airport", "lat": 23.8433, "lon": 90.3978, "country": "BD"},
    {"id": "airport-ktm", "iata": "KTM", "name": "Kathmandu", "type": "airport", "lat": 27.6966, "lon": 85.3591, "country": "NP"},
    {"id": "airport-isb", "iata": "ISB", "name": "Islamabad", "type": "airport", "lat": 33.6161, "lon": 72.8296, "country": "PK"},
    {"id": "airport-khi", "iata": "KHI", "name": "Karachi", "type": "airport", "lat": 24.9065, "lon": 67.1609, "country": "PK"},
    {"id": "airport-lhe", "iata": "LHE", "name": "Lahore", "type": "airport", "lat": 31.5216, "lon": 74.4036, "country": "PK"},
    {"id": "airport-tpe", "iata": "TPE", "name": "Taipei Taoyuan", "type": "airport", "lat": 25.0797, "lon": 121.2342, "country": "TW"},
    {"id": "airport-ctu", "iata": "CTU", "name": "Chengdu", "type": "airport", "lat": 30.5785, "lon": 103.9471, "country": "CN"},
    {"id": "airport-szx", "iata": "SZX", "name": "Shenzhen", "type": "airport", "lat": 22.6393, "lon": 113.8107, "country": "CN"},
    {"id": "airport-xiy", "iata": "XIY", "name": "Xi'an", "type": "airport", "lat": 34.4471, "lon": 108.7516, "country": "CN"},
    {"id": "airport-wuh", "iata": "WUH", "name": "Wuhan", "type": "airport", "lat": 30.7838, "lon": 114.2081, "country": "CN"},
    {"id": "airport-ckg", "iata": "CKG", "name": "Chongqing", "type": "airport", "lat": 29.7193, "lon": 106.6417, "country": "CN"},
    {"id": "airport-hgh", "iata": "HGH", "name": "Hangzhou", "type": "airport", "lat": 30.2295, "lon": 120.4344, "country": "CN"},
    {"id": "airport-nkg", "iata": "NKG", "name": "Nanjing", "type": "airport", "lat": 31.7421, "lon": 118.8620, "country": "CN"},
    {"id": "airport-kmg", "iata": "KMG", "name": "Kunming", "type": "airport", "lat": 24.9924, "lon": 102.7432, "country": "CN"},
    {"id": "airport-csx", "iata": "CSX", "name": "Changsha", "type": "airport", "lat": 28.1892, "lon": 113.2200, "country": "CN"},
    {"id": "airport-urc", "iata": "URC", "name": "Urumqi", "type": "airport", "lat": 43.9071, "lon": 87.4742, "country": "CN"},
    # Oceania
    {"id": "airport-syd", "iata": "SYD", "name": "Sydney", "type": "airport", "lat": -33.9461, "lon": 151.1772, "country": "AU"},
    {"id": "airport-mel", "iata": "MEL", "name": "Melbourne", "type": "airport", "lat": -37.6690, "lon": 144.8410, "country": "AU"},
    {"id": "airport-bne", "iata": "BNE", "name": "Brisbane", "type": "airport", "lat": -27.3842, "lon": 153.1175, "country": "AU"},
    {"id": "airport-per", "iata": "PER", "name": "Perth", "type": "airport", "lat": -31.9403, "lon": 115.9668, "country": "AU"},
    {"id": "airport-adl", "iata": "ADL", "name": "Adelaide", "type": "airport", "lat": -34.9450, "lon": 138.5311, "country": "AU"},
    {"id": "airport-akl", "iata": "AKL", "name": "Auckland", "type": "airport", "lat": -37.0082, "lon": 174.7850, "country": "NZ"},
    {"id": "airport-wlg", "iata": "WLG", "name": "Wellington", "type": "airport", "lat": -41.3272, "lon": 174.8053, "country": "NZ"},
    {"id": "airport-chc", "iata": "CHC", "name": "Christchurch", "type": "airport", "lat": -43.4894, "lon": 172.5322, "country": "NZ"},
    {"id": "airport-nan", "iata": "NAN", "name": "Nadi", "type": "airport", "lat": -17.7554, "lon": 177.4431, "country": "FJ"},
    {"id": "airport-ppt", "iata": "PPT", "name": "Tahiti", "type": "airport", "lat": -17.5537, "lon": -149.6115, "country": "PF"},
    {"id": "airport-gum", "iata": "GUM", "name": "Guam", "type": "airport", "lat": 13.4834, "lon": 144.7961, "country": "GU"},
    {"id": "airport-cns", "iata": "CNS", "name": "Cairns", "type": "airport", "lat": -16.8858, "lon": 145.7554, "country": "AU"},
    {"id": "airport-ool", "iata": "OOL", "name": "Gold Coast", "type": "airport", "lat": -28.1644, "lon": 153.5047, "country": "AU"},
    # Africa
    {"id": "airport-jnb", "iata": "JNB", "name": "Johannesburg", "type": "airport", "lat": -26.1392, "lon": 28.2460, "country": "ZA"},
    {"id": "airport-cpt", "iata": "CPT", "name": "Cape Town", "type": "airport", "lat": -33.9715, "lon": 18.6022, "country": "ZA"},
    {"id": "airport-dur", "iata": "DUR", "name": "Durban", "type": "airport", "lat": -29.6144, "lon": 31.1197, "country": "ZA"},
    {"id": "airport-nbo", "iata": "NBO", "name": "Nairobi", "type": "airport", "lat": -1.3192, "lon": 36.9278, "country": "KE"},
    {"id": "airport-add", "iata": "ADD", "name": "Addis Ababa", "type": "airport", "lat": 8.9779, "lon": 38.7993, "country": "ET"},
    {"id": "airport-los", "iata": "LOS", "name": "Lagos", "type": "airport", "lat": 6.5774, "lon": 3.3212, "country": "NG"},
    {"id": "airport-abj", "iata": "ABJ", "name": "Abidjan", "type": "airport", "lat": 5.2610, "lon": -3.9263, "country": "CI"},
    {"id": "airport-dar", "iata": "DAR", "name": "Dar es Salaam", "type": "airport", "lat": -6.8781, "lon": 39.2026, "country": "TZ"},
    {"id": "airport-acc", "iata": "ACC", "name": "Accra", "type": "airport", "lat": 5.6052, "lon": -0.1668, "country": "GH"},
    {"id": "airport-alg", "iata": "ALG", "name": "Algiers", "type": "airport", "lat": 36.6910, "lon": 3.2154, "country": "DZ"},
    {"id": "airport-tun", "iata": "TUN", "name": "Tunis", "type": "airport", "lat": 36.8510, "lon": 10.2272, "country": "TN"},
    {"id": "airport-cmn", "iata": "CMN", "name": "Casablanca", "type": "airport", "lat": 33.3675, "lon": -7.5898, "country": "MA"},
    {"id": "airport-rak", "iata": "RAK", "name": "Marrakech", "type": "airport", "lat": 31.6069, "lon": -8.0363, "country": "MA"},
    {"id": "airport-mru", "iata": "MRU", "name": "Mauritius", "type": "airport", "lat": -20.4302, "lon": 57.6836, "country": "MU"},
    {"id": "airport-ebb", "iata": "EBB", "name": "Entebbe", "type": "airport", "lat": 0.0424, "lon": 32.4435, "country": "UG"},
    {"id": "airport-kgl", "iata": "KGL", "name": "Kigali", "type": "airport", "lat": -1.9686, "lon": 30.1395, "country": "RW"},
    {"id": "airport-dss", "iata": "DSS", "name": "Dakar", "type": "airport", "lat": 14.6700, "lon": -17.0733, "country": "SN"},
    {"id": "airport-tnr", "iata": "TNR", "name": "Antananarivo", "type": "airport", "lat": -18.7969, "lon": 47.4788, "country": "MG"},
    # South America
    {"id": "airport-gru", "iata": "GRU", "name": "Sao Paulo Guarulhos", "type": "airport", "lat": -23.4356, "lon": -46.4731, "country": "BR"},
    {"id": "airport-gig", "iata": "GIG", "name": "Rio de Janeiro", "type": "airport", "lat": -22.8100, "lon": -43.2505, "country": "BR"},
    {"id": "airport-eze", "iata": "EZE", "name": "Buenos Aires Ezeiza", "type": "airport", "lat": -34.8222, "lon": -58.5358, "country": "AR"},
    {"id": "airport-aep", "iata": "AEP", "name": "Buenos Aires Aeroparque", "type": "airport", "lat": -34.5592, "lon": -58.4156, "country": "AR"},
    {"id": "airport-scl", "iata": "SCL", "name": "Santiago", "type": "airport", "lat": -33.3930, "lon": -70.7858, "country": "CL"},
    {"id": "airport-bog", "iata": "BOG", "name": "Bogota", "type": "airport", "lat": 4.7016, "lon": -74.1469, "country": "CO"},
    {"id": "airport-lim", "iata": "LIM", "name": "Lima", "type": "airport", "lat": -12.0219, "lon": -77.1143, "country": "PE"},
    {"id": "airport-bsb", "iata": "BSB", "name": "Brasilia", "type": "airport", "lat": -15.8711, "lon": -47.9186, "country": "BR"},
    {"id": "airport-cnf", "iata": "CNF", "name": "Belo Horizonte", "type": "airport", "lat": -19.6244, "lon": -43.9719, "country": "BR"},
    {"id": "airport-ssa", "iata": "SSA", "name": "Salvador", "type": "airport", "lat": -12.9086, "lon": -38.3225, "country": "BR"},
    {"id": "airport-rec", "iata": "REC", "name": "Recife", "type": "airport", "lat": -8.1265, "lon": -34.9236, "country": "BR"},
    {"id": "airport-for", "iata": "FOR", "name": "Fortaleza", "type": "airport", "lat": -3.7763, "lon": -38.5326, "country": "BR"},
    {"id": "airport-poa", "iata": "POA", "name": "Porto Alegre", "type": "airport", "lat": -29.9944, "lon": -51.1714, "country": "BR"},
    {"id": "airport-cwb", "iata": "CWB", "name": "Curitiba", "type": "airport", "lat": -25.5285, "lon": -49.1758, "country": "BR"},
    {"id": "airport-vcp", "iata": "VCP", "name": "Campinas", "type": "airport", "lat": -23.0074, "lon": -47.1345, "country": "BR"},
    {"id": "airport-pty", "iata": "PTY", "name": "Panama City", "type": "airport", "lat": 9.0714, "lon": -79.3835, "country": "PA"},
    {"id": "airport-uio", "iata": "UIO", "name": "Quito", "type": "airport", "lat": -0.1292, "lon": -78.3575, "country": "EC"},
    {"id": "airport-mde", "iata": "MDE", "name": "Medellin", "type": "airport", "lat": 6.1645, "lon": -75.4231, "country": "CO"},
    {"id": "airport-ccs", "iata": "CCS", "name": "Caracas", "type": "airport", "lat": 10.6012, "lon": -66.9912, "country": "VE"},
    {"id": "airport-mvd", "iata": "MVD", "name": "Montevideo", "type": "airport", "lat": -34.8384, "lon": -56.0308, "country": "UY"},
    {"id": "airport-asu", "iata": "ASU", "name": "Asuncion", "type": "airport", "lat": -25.2400, "lon": -57.5200, "country": "PY"},
    {"id": "airport-vvi", "iata": "VVI", "name": "Santa Cruz", "type": "airport", "lat": -17.6448, "lon": -63.1354, "country": "BO"},
    {"id": "airport-lpb", "iata": "LPB", "name": "La Paz", "type": "airport", "lat": -16.5133, "lon": -68.1923, "country": "BO"},
    # Caribbean
    {"id": "airport-sju", "iata": "SJU", "name": "San Juan", "type": "airport", "lat": 18.4394, "lon": -66.0018, "country": "PR"},
    {"id": "airport-nas", "iata": "NAS", "name": "Nassau", "type": "airport", "lat": 25.0390, "lon": -77.4662, "country": "BS"},
    {"id": "airport-mbj", "iata": "MBJ", "name": "Montego Bay", "type": "airport", "lat": 18.5037, "lon": -77.9134, "country": "JM"},
    {"id": "airport-kin", "iata": "KIN", "name": "Kingston", "type": "airport", "lat": 17.9357, "lon": -76.7875, "country": "JM"},
    {"id": "airport-pos", "iata": "POS", "name": "Port of Spain", "type": "airport", "lat": 10.5954, "lon": -61.3372, "country": "TT"},
    {"id": "airport-puj", "iata": "PUJ", "name": "Punta Cana", "type": "airport", "lat": 18.5674, "lon": -68.3634, "country": "DO"},
    {"id": "airport-sdq", "iata": "SDQ", "name": "Santo Domingo", "type": "airport", "lat": 18.4297, "lon": -69.6689, "country": "DO"},
    {"id": "airport-hav", "iata": "HAV", "name": "Havana", "type": "airport", "lat": 22.9892, "lon": -82.4091, "country": "CU"},
    {"id": "airport-bgi", "iata": "BGI", "name": "Barbados", "type": "airport", "lat": 13.0746, "lon": -59.4925, "country": "BB"},
    {"id": "airport-anu", "iata": "ANU", "name": "Antigua", "type": "airport", "lat": 17.1367, "lon": -61.7926, "country": "AG"},
    {"id": "airport-sxm", "iata": "SXM", "name": "St Maarten", "type": "airport", "lat": 18.0410, "lon": -63.1089, "country": "SX"},
    {"id": "airport-aua", "iata": "AUA", "name": "Aruba", "type": "airport", "lat": 12.5014, "lon": -70.0152, "country": "AW"},
    {"id": "airport-cur", "iata": "CUR", "name": "Curacao", "type": "airport", "lat": 12.1689, "lon": -68.9598, "country": "CW"},
    {"id": "airport-gcm", "iata": "GCM", "name": "Grand Cayman", "type": "airport", "lat": 19.2928, "lon": -81.3577, "country": "KY"},
    {"id": "airport-stt", "iata": "STT", "name": "St Thomas", "type": "airport", "lat": 18.3373, "lon": -64.9734, "country": "VI"},
    {"id": "airport-tab", "iata": "TAB", "name": "Tobago", "type": "airport", "lat": 11.1497, "lon": -60.8322, "country": "TT"},
]


def load_all_locations() -> list[dict]:
    """Return all location seed data as a flat list of dicts."""
    return MILITARY_BASES + STRATEGIC_CHOKEPOINTS + AIRPORTS


def seed_locations(graph, locations: list[dict] | None = None) -> int:
    """Seed Location nodes into FalkorDB. Idempotent via MERGE.

    Returns the number of locations seeded.
    """
    if locations is None:
        locations = load_all_locations()

    # Batch in chunks to avoid oversized queries
    chunk_size = 50
    total = 0

    for i in range(0, len(locations), chunk_size):
        chunk = locations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $locations AS loc
            MERGE (l:Location {id: loc.id})
            SET l.name = loc.name,
                l.type = loc.type,
                l.lat = loc.lat,
                l.lon = loc.lon,
                l.country = loc.country
            """,
            {"locations": chunk},
        )
        total += len(chunk)

    # Set IATA codes on airports (separate pass since not all locations have iata)
    airports_with_iata = [loc for loc in locations if loc.get("iata")]
    if airports_with_iata:
        for i in range(0, len(airports_with_iata), chunk_size):
            chunk = airports_with_iata[i : i + chunk_size]
            graph.query(
                """
                UNWIND $airports AS apt
                MATCH (l:Location {id: apt.id})
                SET l.iata = apt.iata
                """,
                {"airports": chunk},
            )

    logger.info(f"Seeded {total} Location nodes ({len(MILITARY_BASES)} bases, "
                f"{len(STRATEGIC_CHOKEPOINTS)} chokepoints, {len(AIRPORTS)} airports)")
    return total
