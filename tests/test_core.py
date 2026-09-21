import unittest

from src.core import encoded_body, make_request, redacted_error, safe_gateway_url, validate_response


class CueCoreTests(unittest.TestCase):
    def setUp(self):
        self.request = make_request("req1", "obs:4", "Speaker is ready", ["Camera", "Slides"])

    def test_request_has_only_finite_scenes(self):
        self.assertEqual(self.request["allowedOutcomes"], ["Camera", "Slides"])
        self.assertNotIn(b"api key", encoded_body(self.request))
        with self.assertRaisesRegex(ValueError, "2 to 255"):
            make_request("r", "v", "x", ["Only"])

    def test_validates_full_provenance(self):
        response = {
            "requestId": "req1",
            "revision": "obs:4",
            "record": {
                "schemaVersion": 1,
                "pack": {"name": "obs/scene-cue"},
                "model": "jev-1.13.0",
                "outcome": "Slides",
            },
        }
        self.assertEqual(validate_response(self.request, response), "Slides")
        response["record"]["outcome"] = "Invented"
        with self.assertRaisesRegex(ValueError, "available scene"):
            validate_response(self.request, response)

    def test_url_policy_and_redaction(self):
        self.assertTrue(safe_gateway_url("https://gateway.example/cue"))
        self.assertTrue(safe_gateway_url("http://localhost:8787/cue"))
        self.assertFalse(safe_gateway_url("http://example.com/cue"))
        self.assertNotIn("secret", redacted_error("bad secret\nnext", "secret"))


if __name__ == "__main__":
    unittest.main()
