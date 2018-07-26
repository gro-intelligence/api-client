import os
import unicodecsv
import api.client.lib

API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN=os.environ['GROAPI_TOKEN']

client = api.client.Client(API_HOST, ACCESS_TOKEN)

def output_data_points_to_csv(data_points):
    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))
    for point in data_points:
        writer.writerow([
            point['start_date'],
            point['end_date'],
            point['value'],
            # input_unit_id is metadata for the point which refers to the unit the source reported
            # it in originally. The following line translates the Gro id number for that unit into a
            # human-readable abbreviation like kg or km^2
            client.lookup_unit_abbreviation(point['input_unit_id'])
        ])
    print('Your data has been written to ' + OUTPUT_FILENAME)

def main():

    # search_and_lookup returns many results in descending order of relevance, so in each case
    # we will just take the first one
    cape_verde_id, cape_verde_type = list(client.search('cape verde'))[0]

    # you can also specify the type if you want. In this case, we know management of donkey manure
    # should be an item. Note the output is now just an id rather than an id and a type
    manure_id = list(client.search('management of donkey manure', 'items'))[0]

    # you can also lookup the results and see the names of these ids before you decide to use them
    # either by using the client.search() function and then the client.lookup() function OR by using
    # the client.search_and_lookup() helper utility
    for entity_id, entity_type in client.search('emissions quantity'):
        # In this case, we actually want "Total Emissions Quantity (mass)" so let's look for that
        # one in the results
        entity_details = client.lookup(entity_type, entity_id)
        if entity_details['name'] == 'Total Emissions Quantity (mass)':
            emissions_id = entity_id
            break

    # A data series, as Gro defines it, consists of a metric, item, region, source, and frequency.
    # There is also sometimes a 6th entity type, partnerRegion, which applies when multiple the
    # series refers to an interaction between two regions (importer & exporter, for example)
    # You may select any subset of these 6 parameters and find relevant data series. Here, we will
    # select the three most important: metric, item, and region
    selected_entities = { u'region_id': cape_verde_id,
                          u'item_id': manure_id,
                          u'metric_id': emissions_id  }

    print('Your selections: ' + str(selected_entities))

    # Get what possible series there are for that combination of selections - there may be multiple
    # possibilities, from different sources, different frequencies, etc.
    possible_data_series = list(client.get_data_series(**selected_entities))
    print('Your possible data series: ' + str(possible_data_series))

    # get_data_series doesn't rank the series since you very well might just want all of them, but
    # for our example, let's  use a ranking function to try to pick just the "best" one ("best" is a
    # combination of recency of data, how far back the data goes, and how many data points are
    # available):
    best_data_series = list(client.rank_series_by_source(possible_data_series))[0]
    print('Your best data series: ' + str(possible_data_series))

    # You can add a time range restriction to your data request (Optional - otherwise get all points)
    best_data_series['start_date'] = '2000-01-01'
    best_data_series['end_date'] = '2012-12-31'

    # Get an array of data_points for your chosen data_series
    data_points = list(client.get_data_points(**best_data_series))

    # You can output this list of points to any format you'd like, and we provide a helper function
    # for outputting to a pandas dataframe, but here is a simple example of how you might write it
    # to a CSV file:
    output_data_points_to_csv(data_points)

if __name__ == "__main__":
    main()
