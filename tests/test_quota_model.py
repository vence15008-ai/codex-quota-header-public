import unittest
from quota_model import quota_view, remaining


class QuotaTests(unittest.TestCase):
    def window(self, minutes, used, reset=1800000000):
        return dict(windowDurationMins=minutes, usedPercent=used, resetsAt=reset)

    def payload(self, primary, secondary=None):
        return {"rateLimitsByLimitId": {"codex": {"primary": primary, "secondary": secondary}}}

    def test_duration_not_field_order(self):
        view = quota_view(self.payload(self.window(300, 20), self.window(10080, 40)))
        self.assertEqual(view['week']['remaining'], 60)
        self.assertEqual(view['short']['remaining'], 80)

    def test_pro_without_short(self):
        view = quota_view(self.payload(self.window(10080, 15)))
        self.assertIsNone(view['short'])
        self.assertIsNone(view['reserve'])

    def test_reserve(self):
        payload = self.payload(self.window(10080, 0))
        payload['rateLimitsByLimitId']['base_model_inference'] = {'primary': self.window(10080, 23)}
        self.assertEqual(quota_view(payload)['reserve']['remaining'], 77)

    def test_legacy(self):
        view = quota_view({'rateLimits': {'primary': {'usedPercent': 2}, 'secondary': {'usedPercent': 30}}})
        self.assertEqual(view['week']['remaining'], 70)

    def test_known_short_never_week(self):
        with self.assertRaises(ValueError):
            quota_view(self.payload(self.window(300, 12)))

    def test_missing_and_non_finite(self):
        self.assertIsNone(remaining({'usedPercent': None}))
        with self.assertRaises(ValueError): remaining({'usedPercent': float('nan')})
        with self.assertRaises(ValueError): quota_view({})

    def test_clamp(self):
        self.assertEqual(remaining({'usedPercent': 130}), 0)
        self.assertEqual(remaining({'usedPercent': -10}), 100)

    def test_invalid_payload_shapes(self):
        for payload in (None, [], {'rateLimitsByLimitId': []}, {'rateLimitsByLimitId': {'codex': 'bad'}}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                quota_view(payload)

    def test_bad_percent_and_reset(self):
        for value in (True, {}, 'invalid', float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                remaining({'usedPercent': value})
        for reset in (True, 'invalid', float('inf'), -1, 1e20):
            view = quota_view(self.payload(self.window(10080, 12, reset)))
            self.assertIsNone(view['week']['resetsAt'])


if __name__ == '__main__': unittest.main()
