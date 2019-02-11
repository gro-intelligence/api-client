import numpy as np
import unittest
from datetime import datetime
from api.client.samples.similar_regions.transform import _fill_in_blank_days, FourierCoef

class TransformTests(unittest.TestCase):

    def setUp(self):
        self.fourier = FourierCoef(0, 10)
        pass

    def test_fill_in_days(self):

        fake_pulled_dataset = [{u'value': 1, u'start_date': u'2018-09-23T00:00:00.000Z'},
                               {u'value': 2, u'start_date': u'2018-09-24T00:00:00.000Z'},
                               {u'value': 3, u'start_date': u'2018-09-25T00:00:00.000Z'},
                               {u'value': 4, u'start_date': u'2018-09-26T00:00:00.000Z'},
                               {u'value': 5, u'start_date': u'2018-09-28T00:00:00.000Z'},
                               {u'value': 6, u'start_date': u'2018-09-29T00:00:00.000Z'}]

        start_datetime = datetime(2018, 9, 25)

        np.testing.assert_equal(_fill_in_blank_days(10, start_datetime, fake_pulled_dataset),
                         np.array([3.0, 4.0, float('NaN'), 5.0, 6.0, float('NaN'),
                          float('NaN'), float('NaN'), float('NaN'), float('NaN')]))

        return

    def test_fourier(self):

        # we want to make sure we test phase independance here as well

        x = np.linspace(-np.pi, np.pi, 201)
        y = np.sin(5*x)
        coef = self.fourier.transform(y)

        y_with_phase = np.sin(5*x+0.2345)
        coef_with_phase = self.fourier.transform(y_with_phase)

        # the biggest coef should be the same...
        self.assertEqual(np.argmax(coef), np.argmax(coef_with_phase))

        # We shouldn't have big discrepancies
        np.testing.assert_allclose(coef, coef_with_phase, rtol=1e-0, atol=0)


if __name__ == '__main__':
    unittest.main()
