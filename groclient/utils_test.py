from unittest import TestCase

from groclient.utils import (
    str_camel_to_snake,
    str_snake_to_camel,
    dict_reformat_keys,
    dict_unnest,
    list_chunk,
    intersect,
    zip_selections,
)


class UtilsTests(TestCase):
    def test_str_camel_to_snake(self):
        self.assertEqual(str_camel_to_snake("partnerRegionId"), "partner_region_id")

        self.assertEqual(str_camel_to_snake("partner_region_id"), "partner_region_id")

    def test_str_snake_to_camel(self):
        self.assertEqual(str_snake_to_camel("hello_world"), "helloWorld")

    def test_dict_reformat_keys(self):
        self.assertEqual(
            dict_reformat_keys({"belongsTo": {"metricId": 4}}, str_camel_to_snake),
            {"belongs_to": {"metricId": 4}},
        )

        self.assertEqual(
            dict_reformat_keys({"belongs_to": {"metric_id": 4}}, str_snake_to_camel),
            {"belongsTo": {"metric_id": 4}},
        )

    def test_dict_unnest(self):
        self.assertEqual(
            dict_unnest({"metric_id": 14, "belongs_to": {"metric_id": 14}}),
            {"metric_id": 14, "belongs_to_metric_id": 14},
        )

        self.assertEqual(
            dict_unnest(
                {
                    "metric_id": 14,
                    "belongs_to": {
                        "metric_id": 14,
                        "metadata": {"includes_historical": True},
                    },
                }
            ),
            {
                "metric_id": 14,
                "belongs_to_metric_id": 14,
                "belongs_to_metadata_includes_historical": True,
            },
        )

    def test_list_chunk(self):
        self.assertEqual(
            list_chunk([1, 2, 3, 4, 5, 6, 7, 8], 3), [[1, 2, 3], [4, 5, 6], [7, 8]]
        )
        self.assertEqual(
            list_chunk([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 5),
            [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11]],
        )

    def test_intersect(self):
        self.assertEqual(intersect([1, 2, 3], [4, 5, 6]), [])
        self.assertEqual(intersect([1, 2, 3], [4, 5, 6, 2]), [2])
        self.assertEqual(intersect([1, 2, 3], [1, 2, 3]), [1, 2, 3])

    def test_zip_selections(self):
        self.assertEqual(
            zip_selections([860032, 274, 1215, 0, 2, 9]),
            {
                "metric_id": 860032,
                "item_id": 274,
                "region_id": 1215,
                "partner_region_id": 0,
                "frequency_id": 2,
                "source_id": 9,
            },
        )
        self.assertEqual(
            zip_selections(
                [860032, 274, 1215, 0, 2, 9], insert_nulls=True, metric_id=1
            ),
            {
                "metric_id": 860032,
                "item_id": 274,
                "region_id": 1215,
                "partner_region_id": 0,
                "frequency_id": 2,
                "source_id": 9,
                "insert_nulls": True,
            },
        )
