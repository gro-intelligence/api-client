# If you're running the first time, run these three lines. Alternatively download the pre-computed version from
# here:
import csv

from api.client.samples.similar_regions.region_properties import region_properties
from api.client.samples.similar_regions.similar_region import SimilarRegion

usa_states = [1215, 13100, 13061, 13053, 13099, 13069, 13091, 13076, 13064, 13060, 13101, 13057, 13067, 13077, 13056, 13065, 13093, 13097, 13059, 13054, 13062, 13070, 13055, 13071, 13080, 13052, 13079, 13089, 13075, 13058, 13072, 13051, 13087, 13082, 13088, 13092, 13074, 13068, 13095, 13085, 13078, 13066, 13090, 13063, 13086, 13084, 13083, 13098, 13081, 13096, 13094, 13073]
sim = SimilarRegion(region_properties, regions_to_compare=usa_states)

csv_output = True

if csv_output:
    level_suffix = "" if requested_level is None else "_level_" + str(requested_level)
    f = open("output/" + str(region_id) + level_suffix + ".csv", 'wb')
    csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

for result in sim.similar_to(1215):
    print(result)

    if csv_output:
        output = [district_name, province["name"], country["name"]]
        output = [unicode(s).encode("utf-8") for s in output]
        csv_writer.writerow(output)


