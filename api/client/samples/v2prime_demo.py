import os
from groclient.experimental import Experimental
from groclient import GroClient
from datetime import datetime
import pandas as pd

API_HOST = "apistage11201.gro-intelligence.com"
ACCESS_TOKEN = os.environ["GROAPI_TOKEN_STAGE"]


exp_client = Experimental(API_HOST, ACCESS_TOKEN)
client = GroClient(API_HOST, ACCESS_TOKEN)


def simple_example():
    exp_client = Experimental(API_HOST, ACCESS_TOKEN)
    selection = {
        "metric_id": 2540047,
        "item_ids": [3457],
        "region_ids": [1215],
        "source_id": 26,
        "frequency_id": 1,
        "start_date": "2023-03-01",
    }

    res = exp_client.get_data_points(**selection)
    sample_ds_res = res["data_series"][0]
    print("------sample results (simple request)------")
    print("1st series info:")
    print(sample_ds_res["series_description"])
    data_df = pd.DataFrame(
        sample_ds_res["data_points"],
        columns=["start_timestamp", "end_timestamp", "value"],
    )
    print("1st series data:")
    print(data_df.head(10))


def print_start_msg(idx, tc):
    print(
        f"------example {idx+1}: (source_id: {tc['source']}, region_num: {len(tc['region'])}, {tc['start']} to {tc['end']} )-----"
    )


def print_stats(endpoint, start, end, data_count):
    time_diff = (end - start).total_seconds()
    ms_per_point = (1000 * time_diff) / data_count
    print(
        f"version: {endpoint}\ntotal_data_points: {data_count}\ntime_spent(s): {time_diff}\nms per points: {ms_per_point}\n"
    )


def get_test_cases(apiclient):
    L5_US = apiclient.get_descendant(
        entity_type="regions",
        entity_id=1215,
        descendant_level=5,
        include_details=False,
        include_historical=False,
    )
    L5_US_IDS = [r["id"] for r in L5_US]

    return [
        {
            "metric": 431132,
            "item": 321,
            "source": 3,
            "frequency": 3,
            "start": "2022-01-01",
            "end": "2023-01-01",
            "region": [
                11011,
                11012,
                11013,
                11014,
                11015,
                11016,
                11017,
                11018,
                11019,
                11020,
            ],
        },
        {
            "metric": 2540047,
            "item": 3457,
            "source": 26,
            "frequency": 1,
            "start": "2000-01-01",
            "end": "2023-04-01",
            "region": [1215],
        },
        {
            "metric": 2540047,
            "item": 3457,
            "source": 26,
            "frequency": 1,
            "start": "2022-8-01",
            "end": "2022-12-01",
            "region": L5_US_IDS[0:500],
        },
        # {
        #     "metric": 15851824,
        #     "item": 780,
        #     "source": 235,
        #     "frequency": 1,
        #     "start": "2005-01-03",
        #     "end": "2023-01-03",
        #     "region": [
        #         137446,
        #         137380,
        #         139273,
        #         138266,
        #         138848,
        #         137016,
        #         139224,
        #         138435,
        #         138418,
        #         139130,
        #     ],
        # },
    ]


def build_v1_selection(tc):
    return {
        "item_id": tc["item"],
        "metric_id": tc["metric"],
        "source_id": tc["source"],
        "frequency_id": tc["frequency"],
        "start_date": tc["start"],
        "end_date": tc["end"],
        "region_id": tc["region"],
    }


def build_v2_selection(tc):
    return {
        "item_ids": tc["item"],
        "metric_id": tc["metric"],
        "source_id": tc["source"],
        "frequency_id": tc["frequency"],
        "start_date": tc["start"],
        "end_date": tc["end"],
        "region_ids": tc["region"],
    }


def perf_comparison():
    exp_client = Experimental(API_HOST, ACCESS_TOKEN)
    client = GroClient(API_HOST, ACCESS_TOKEN)

    END_POINTS = ["v2/data", "v2prime/data"]
    for idx, tc in enumerate(get_test_cases(client)):
        print_start_msg(idx, tc)
        for endpoint in END_POINTS:
            start = datetime.now()
            data_count = 0
            if endpoint == "v2/data":
                selection = build_v1_selection(tc)
                res = client.get_data_points(**selection)
                data_count = len(res)
            else:
                selection = build_v2_selection(tc)
                res = exp_client.get_data_points(**selection)
                for ds in res["data_series"]:
                    data_count += len(ds["data_points"])

            end = datetime.now()
            print_stats(endpoint, start, end, data_count)


def main():
    simple_example()
    # perf_comparison()


if __name__ == "__main__":
    main()
