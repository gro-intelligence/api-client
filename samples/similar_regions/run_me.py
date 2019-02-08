import argparse
import unicodecsv as csv
from api.client.samples.similar_regions.region_properties import region_properties
from api.client.samples.similar_regions.similar_region import SimilarRegion

USA_STATES = [1215, 13100, 13061, 13053, 13099, 13069, 13091, 13076, 13064, 13060, 13101, 13057, 13067, 13077, 13056, 13065, 13093, 13097, 13059, 13054, 13062, 13070, 13055, 13071, 13080, 13052, 13079, 13089, 13075, 13058, 13072, 13051, 13087, 13082, 13088, 13092, 13074, 13068, 13095, 13085, 13078, 13066, 13090, 13063, 13086, 13084, 13083, 13098, 13081, 13096, 13094, 13073]


def main():
    parser = argparse.ArgumentParser(description="Gro Similar Regions")
    parser.add_argument("--region_id", required=True, type=int)
    parser.add_argument("--csv_output", default=True)
    parser.add_argument("--region_level", default=None)
    parser.add_argument("--num_regions", default=10)
    args = parser.parse_args()

    sim = SimilarRegion(region_properties, regions_to_compare=USA_STATES)
    if args.csv_output:
        level_suffix = "" if not args.region_level else "_level_" + str(args.region_level)
        f = open(str(args.region_id) + level_suffix + ".csv", 'wb')
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for output in sim.similar_to(args.region_id, args.num_regions, args.region_level):
        if args.csv_output:
            csv_writer.writerow(output)
        else:
            print(output)


if __name__ == "__main__":
    main()
