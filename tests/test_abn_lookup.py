import io
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.abn_lookup import (
    ABNLookupError,
    MissingCredentialsError,
    compare_entity_name,
    extract_abn,
    is_valid_abn,
    lookup_by_abn,
    search_by_name,
    verify_business,
)


VALID_ABN = "51835430479"
ACTIVE_RESPONSE = b"""<?xml version="1.0"?>
<ABRPayloadSearchResults xmlns="http://abr.business.gov.au/ABRXMLSearch/">
  <response><businessEntity>
    <ABN><identifierValue>51835430479</identifierValue></ABN>
    <entityStatus><entityStatusCode>Active</entityStatusCode>
      <effectiveFrom>2000-01-01</effectiveFrom></entityStatus>
    <entityType><entityDescription>Australian Private Company</entityDescription></entityType>
    <goodsAndServicesTax><effectiveFrom>2001-07-01</effectiveFrom></goodsAndServicesTax>
    <mainName><organisationName>Example Pty Ltd</organisationName></mainName>
    <mainBusinessPhysicalAddress><stateCode>VIC</stateCode></mainBusinessPhysicalAddress>
  </businessEntity></response>
</ABRPayloadSearchResults>"""
CANCELLED_RESPONSE = ACTIVE_RESPONSE.replace(b"Active", b"Cancelled")
NAME_RESPONSE = b"""<?xml version="1.0"?>
<ABRPayloadSearchResults xmlns="http://abr.business.gov.au/ABRXMLSearch/">
  <response><searchResultsList>
    <searchResultsRecord><ABN>51835430479</ABN>
      <matchingName>Example Pty Ltd</matchingName>
      <ABNStatus>Active</ABNStatus><stateCode>VIC</stateCode>
      <matchScore>100</matchScore></searchResultsRecord>
    <searchResultsRecord><ABN>53004085616</ABN>
      <matchingName>Example Services</matchingName>
      <ABNStatus>Cancelled</ABNStatus><stateCode>NSW</stateCode>
      <matchScore>80</matchScore></searchResultsRecord>
  </searchResultsList></response>
</ABRPayloadSearchResults>"""
NOT_FOUND_RESPONSE = b"""<ABRPayloadSearchResults>
  <response><exception><exceptionCode>SEARCH</exceptionCode>
    <exceptionDescription>No records found</exceptionDescription></exception></response>
</ABRPayloadSearchResults>"""


class TestABNValidation(unittest.TestCase):
    def test_valid_abn_checksum(self):
        self.assertTrue(is_valid_abn(VALID_ABN))

    def test_abn_with_spaces_has_valid_checksum(self):
        self.assertTrue(is_valid_abn("51 835 430 479"))

    def test_invalid_abn_checksum(self):
        self.assertFalse(is_valid_abn("51835430470"))

    def test_extract_abn_from_ad(self):
        self.assertEqual(
            extract_abn("Employer ABN: 51 835 430 479. Apply online."),
            VALID_ABN,
        )

    def test_no_abn_found(self):
        self.assertEqual(extract_abn("No business number is included."), "")


class TestABNLookup(unittest.TestCase):
    def mock_response(self, payload):
        return io.BytesIO(payload)

    @patch("src.abn_lookup.urlopen")
    def test_abn_only_search_active_record(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(ACTIVE_RESPONSE)
        entity = lookup_by_abn(VALID_ABN, authentication_guid="test-guid")
        self.assertEqual(entity["abn"], VALID_ABN)
        self.assertEqual(entity["status"], "Active")
        self.assertEqual(entity["entity_name"], "Example Pty Ltd")
        self.assertEqual(entity["entity_type"], "Australian Private Company")
        self.assertEqual(entity["gst_status"], "Registered")
        self.assertEqual(entity["state"], "VIC")
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith(
            "/SearchByABNv202001"
        ))
        self.assertNotIn("test-guid", request.full_url)
        self.assertIn(b"authenticationGuid=test-guid", request.data)

    @patch("src.abn_lookup.urlopen")
    def test_cancelled_abn_response(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(CANCELLED_RESPONSE)
        entity = lookup_by_abn(VALID_ABN, authentication_guid="test-guid")
        self.assertEqual(entity["status"], "Cancelled")

    @patch("src.abn_lookup.urlopen")
    def test_abn_not_found(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NOT_FOUND_RESPONSE)
        with self.assertRaisesRegex(ABNLookupError, "No matching"):
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")

    @patch("src.abn_lookup.urlopen")
    def test_company_name_only_search_returns_multiple_matches(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NAME_RESPONSE)
        matches = search_by_name("Example", authentication_guid="test-guid")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["entity_name"], "Example Pty Ltd")
        self.assertEqual(matches[1]["status"], "Cancelled")
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith(
            "/ABRSearchByNameAdvancedSimpleProtocol2017"
        ))

    @patch("src.abn_lookup.urlopen")
    def test_company_name_not_found(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NOT_FOUND_RESPONSE)
        with self.assertRaisesRegex(ABNLookupError, "No matching"):
            search_by_name("No Such Company", authentication_guid="test-guid")

    def test_matching_company_name_comparison(self):
        result = compare_entity_name("Example Pty Ltd", "Example Pty Ltd")
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["similarity"], 1.0)

    def test_different_company_name_comparison(self):
        result = compare_entity_name("Example Pty Ltd", "Other Group")
        self.assertEqual(result["status"], "different")

    @patch("src.abn_lookup.lookup_by_abn")
    def test_combined_abn_and_company_name_search(self, mocked_lookup):
        mocked_lookup.return_value = {
            "abn": VALID_ABN,
            "entity_name": "Example Pty Ltd",
        }
        result = verify_business(
            VALID_ABN,
            "Example Pty Ltd",
            authentication_guid="test-guid",
        )
        self.assertEqual(result["mode"], "abn")
        self.assertEqual(result["name_comparison"]["status"], "exact")
        mocked_lookup.assert_called_once()

    @patch("src.abn_lookup.search_by_name")
    def test_name_only_verification(self, mocked_search):
        mocked_search.return_value = [{"abn": VALID_ABN}]
        result = verify_business(
            company_name="Example",
            authentication_guid="test-guid",
        )
        self.assertEqual(result["mode"], "name")
        self.assertEqual(result["matches"][0]["abn"], VALID_ABN)

    def test_no_search_input(self):
        with self.assertRaisesRegex(ABNLookupError, "Enter an ABN"):
            verify_business()

    @patch("src.abn_lookup.urlopen", side_effect=URLError("private detail"))
    def test_api_connection_failure_is_sanitised(self, mocked_urlopen):
        with self.assertRaisesRegex(ABNLookupError, "Could not connect"):
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")

    def test_missing_authentication_guid(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(MissingCredentialsError):
                lookup_by_abn(VALID_ABN)

    @patch("src.abn_lookup.urlopen", side_effect=TimeoutError())
    def test_api_timeout_is_sanitised(self, mocked_urlopen):
        with self.assertRaisesRegex(ABNLookupError, "Could not connect"):
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")

    @patch("src.abn_lookup.urlopen")
    def test_unexpected_api_response(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(b"<not-xml")
        with self.assertRaisesRegex(ABNLookupError, "unexpected response"):
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")


if __name__ == "__main__":
    unittest.main()
