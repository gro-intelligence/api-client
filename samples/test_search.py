import argparse
import os
import unicodecsv
import api.client as gro_client


ENV = 'dev'

API_HOSTS = {
    'local': '127.0.0.1:5000',
    'dev': 'apidev11201.gro-intelligence.com',
    'stage': 'apistage11201.gro-intelligence.com',
    'prod': 'api.gro-intelligence.com',
}

ACCESS_TOKENS = {
    'local': os.environ['GROAPI_TOKEN_DEV'],
    'dev': os.environ['GROAPI_TOKEN_DEV'],
    'stage': os.environ['GROAPI_TOKEN_STAGE'],
    'prod': os.environ['GROAPI_TOKEN']
}

API_HOST = API_HOSTS[ENV]
ACCESS_TOKEN = ACCESS_TOKENS[ENV]

MAX_NUM_RESULTS = 20
def run_universal_test():
    print "RUNNING 'universal' SEARCH"
    while True:
        print '\n\n-------------------------'
        term = raw_input("What's your search term?: ")
        id_results = gro_client.lib.universal_search(
            ACCESS_TOKEN, API_HOST, term)[:MAX_NUM_RESULTS]
        for result in id_results:
              print '{}: {}'.format(
                result[1],
                gro_client.lib.lookup(ACCESS_TOKEN, API_HOST, result[1]+'s',
                                      result[0])['name'].encode('utf-8'))


def run_search_by_type_test(entity_type):
    type_formatted = entity_type if entity_type[-1] == 's' else entity_type+'s'
    print "RUNNING '{}' SEARCH".format(type_formatted)
    client = gro_client.Client(API_HOST, ACCESS_TOKEN)

    while True:
        print '\n\n-------------------------'
        term = raw_input("What's your search term?: ")
        count = 0
        for i in client.search_and_lookup(type_formatted, term):
            print i['name']
            count += 1
            if count >= MAX_NUM_RESULTS:
                break


def main(entity_type):
    if entity_type:
        run_search_by_type_test(entity_type)
    else:
        run_universal_test()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--type', default=None,
        help='search by specific entity type (metric, item, region, source)')
    args = parser.parse_args()
    main(args.type)
