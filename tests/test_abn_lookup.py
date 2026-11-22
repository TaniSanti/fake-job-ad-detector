import io
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.abn_lookup import (
    ABNLookupError,
    ABN_NOT_FOUND_MESSAGE,
    COMPANY_NAME_NOT_FOUND_MESSAGE,
    INVALID_ABN_MESSAGE,
    MissingCredentialsError,
    compare_entity_name,
    extract_abn,
    format_name_match,
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
INDIVIDUAL_WITH_BUSINESS_NAME_RESPONSE = b"""<?xml version="1.0"?>
<ABRPayloadSearchResults xmlns="http://abr.business.gov.au/ABRXMLSearch/">
  <response><businessEntity>
    <ABN><identifierValue>75584950135</identifierValue></ABN>
    <entityStatus><entityStatusCode>Active</entityStatusCode></entityStatus>
    <entityType><entityDescription>Individual/Sole Trader</entityDescription></entityType>
    <legalName><givenName>DAVINA</givenName><familyName>TALAKAI</familyName></legalName>
    <businessName><organisationName>Taste &amp; See Community Outreach</organisationName></businessName>
  </businessEntity></response>
</ABRPayloadSearchResults>"""
NAME_RESPONSE = b"""<?xml version="1.0"?>
<ABRPayloadSearchResults xmlns="http://abr.business.gov.au/ABRXMLSearch/">
  <response><searchResultsList>
    <searchResultsRecord><ABN>51835430479</ABN>
      <fullName>Example Pty Ltd</fullName>
      <identifierStatus>Active</identifierStatus><stateCode>VIC</stateCode>
      <score>100</score></searchResultsRecord>
    <searchResultsRecord><ABN>53004085616</ABN>
      <fullName>Example Services</fullName>
      <identifierStatus>Cancelled</identifierStatus><stateCode>NSW</stateCode>
      <score>80</score></searchResultsRecord>
  </searchResultsList></response>
</ABRPayloadSearchResults>"""
DAVINA_NAME_RESPONSE = b"""<?xml version="1.0"?>
<ABRPayloadSearchResults xmlns="http://abr.business.gov.au/ABRXMLSearch/">
  <response><searchResultsList>
    <searchResultsRecord><ABN>51835430479</ABN>
      <fullName>DAVINA PTY LIMITED</fullName></searchResultsRecord>
    <searchResultsRecord><ABN>53004085616</ABN>
      <fullName>The Trustee for Davina</fullName></searchResultsRecord>
    <searchResultsRecord><ABN>12345678901</ABN>
      <fullName>Davina Holdings Australia</fullName></searchResultsRecord>
    <searchResultsRecord><ABN>12345678901</ABN>
      <fullName>Local Care Davina</fullName></searchResultsRecord>
    <searchResultsRecord><ABN>98765432109</ABN>
      <fullName>Dee Dee's Dream</fullName></searchResultsRecord>
    <searchResultsRecord><ABN>11111111111</ABN>
      <fullName>Unrelated matched name</fullName>
      <mainName><organisationName>Registered Davina Ventures</organisationName></mainName>
    </searchResultsRecord>
  </searchResultsList></response>
</ABRPayloadSearchResults>"""
NOT_FOUND_RESPONSE = b"""<ABRPayloadSearchResults>
  <response><exception><exceptionCode>SEARCH</exceptionCode>
    <exceptionDescription>No records found</exceptionDescription></exception></response>
</ABRPayloadSearchResults>"""
AUTHENTICATION_FAILURE_RESPONSE = b"""<ABRPayloadSearchResults>
  <response><exception><exceptionCode>AUTHENTICATION</exceptionCode>
    <exceptionDescription>The GUID mock-only-guid is not recognised.</exceptionDescription>
  </exception></response>
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
    def test_individual_legal_name_preferred_to_business_name(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(
            INDIVIDUAL_WITH_BUSINESS_NAME_RESPONSE
        )
        entity = lookup_by_abn("75584950135", authentication_guid="test-guid")
        self.assertEqual(entity["entity_name"], "TALAKAI, DAVINA")
        self.assertNotEqual(entity["entity_name"], "Taste & See Community Outreach")

    @patch("src.abn_lookup.urlopen")
    def test_abn_not_found(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NOT_FOUND_RESPONSE)
        with self.assertRaisesRegex(ABNLookupError, "no record for this ABN") as error:
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")
        self.assertEqual(str(error.exception), ABN_NOT_FOUND_MESSAGE)

    def test_invalid_abn_error_uses_plain_language(self):
        with self.assertRaises(ABNLookupError) as error:
            lookup_by_abn("12345678992", authentication_guid="test-guid")
        self.assertEqual(str(error.exception), INVALID_ABN_MESSAGE)
        self.assertNotIn("checksum", str(error.exception).casefold())

    @patch("src.abn_lookup.urlopen")
    def test_company_name_only_search_returns_multiple_matches(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NAME_RESPONSE)
        matches = search_by_name("Example", authentication_guid="test-guid")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["matching_name"], "Example Pty Ltd")
        self.assertEqual(matches[1]["matching_name"], "Example Services")
        self.assertEqual(matches[0]["status"], "Active")
        self.assertEqual(matches[1]["status"], "Cancelled")
        self.assertEqual(matches[0]["match_score"], "100")
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith(
            "/ABRSearchByNameAdvancedSimpleProtocol2017"
        ))
        self.assertIn(b"searchWidth=Typical", request.data)
        self.assertIn(b"minimumScore=50", request.data)
        self.assertIn(b"maxSearchResults=200", request.data)
        self.assertIn(b"legalName=Y", request.data)
        self.assertIn(b"businessName=Y", request.data)
        self.assertIn(b"tradingName=Y", request.data)

    @patch("src.abn_lookup.urlopen")
    def test_name_search_keeps_all_returned_names_containing_query(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(DAVINA_NAME_RESPONSE)
        matches = search_by_name("davina", authentication_guid="test-guid")
        self.assertEqual(
            [match["matching_name"] for match in matches],
            [
                "DAVINA PTY LIMITED",
                "The Trustee for Davina",
                "Davina Holdings Australia",
                "Local Care Davina",
                "Registered Davina Ventures",
            ],
        )

    def test_dropdown_shows_only_name_and_abn(self):
        label = format_name_match({
            "matching_name": "DAVINA PTY LIMITED",
            "entity_name": "Another Legal Name Pty Ltd",
            "abn": "51835430479",
            "status": "Cancelled",
        })
        self.assertEqual(label, "DAVINA PTY LIMITED — ABN 51835430479")

    @patch("src.abn_lookup.urlopen")
    def test_company_name_not_found(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(NOT_FOUND_RESPONSE)
        with self.assertRaisesRegex(ABNLookupError, "no matching business name") as error:
            search_by_name("No Such Company", authentication_guid="test-guid")
        self.assertEqual(str(error.exception), COMPANY_NAME_NOT_FOUND_MESSAGE)

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

    @patch("src.abn_lookup.lookup_by_abn")
    @patch("src.abn_lookup.search_by_name")
    def test_name_only_verification_fills_entity_name_from_cancelled_abn(
        self, mocked_search, mocked_lookup
    ):
        mocked_search.return_value = [{"abn": VALID_ABN, "entity_name": ""}]
        mocked_lookup.return_value = {
            "abn": VALID_ABN,
            "entity_name": "Davina Example",
            "status": "Cancelled",
        }
        result = verify_business(
            company_name="Example",
            authentication_guid="test-guid",
        )
        self.assertEqual(result["mode"], "name")
        self.assertEqual(result["matches"][0]["abn"], VALID_ABN)
        self.assertEqual(result["matches"][0]["entity_name"], "Davina Example")
        self.assertEqual(result["matches"][0]["status"], "Cancelled")
        mocked_lookup.assert_called_once_with(
            VALID_ABN,
            authentication_guid="test-guid",
            secrets=None,
        )

    @patch("src.abn_lookup.lookup_by_abn", side_effect=ABNLookupError("temporary"))
    @patch("src.abn_lookup.search_by_name")
    def test_name_only_search_survives_failed_name_enrichment(
        self, mocked_search, mocked_lookup
    ):
        mocked_search.return_value = [{"abn": VALID_ABN, "entity_name": ""}]
        result = verify_business(
            company_name="Example",
            authentication_guid="test-guid",
        )
        self.assertEqual(result["matches"][0]["abn"], VALID_ABN)
        self.assertEqual(result["matches"][0]["entity_name"], "")

    def test_no_search_input(self):
        with self.assertRaisesRegex(ABNLookupError, "Enter an ABN"):
            verify_business()

    @patch("src.abn_lookup.urlopen", side_effect=URLError("private detail"))
    def test_api_connection_failure_is_sanitised(self, mocked_urlopen):
        with self.assertRaisesRegex(
            ABNLookupError, "Could not connect to the ABR service"
        ) as error:
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")
        self.assertIn("try again", str(error.exception))
        self.assertNotIn("private detail", str(error.exception))

    def test_missing_authentication_guid(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.abn_lookup.urlopen") as mocked_urlopen:
                with self.assertRaises(MissingCredentialsError) as error:
                    lookup_by_abn(VALID_ABN)
        self.assertIn("not configured", str(error.exception))
        self.assertIn("ABR_AUTHENTICATION_GUID", str(error.exception))
        mocked_urlopen.assert_not_called()

    @patch("src.abn_lookup.urlopen")
    def test_api_authentication_failure_is_sanitised(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(
            AUTHENTICATION_FAILURE_RESPONSE
        )
        fake_guid = "mock-only-guid"
        with self.assertRaisesRegex(
            ABNLookupError, "could not complete this search"
        ) as error:
            lookup_by_abn(VALID_ABN, authentication_guid=fake_guid)
        self.assertIn("try again later", str(error.exception))
        self.assertNotIn(fake_guid, str(error.exception))
        mocked_urlopen.assert_called_once()

    @patch("src.abn_lookup.urlopen", side_effect=TimeoutError())
    def test_api_timeout_is_sanitised(self, mocked_urlopen):
        with self.assertRaisesRegex(
            ABNLookupError, "Could not connect to the ABR service"
        ) as error:
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")
        self.assertIn("try again", str(error.exception))

    @patch("src.abn_lookup.urlopen")
    def test_unexpected_api_response(self, mocked_urlopen):
        mocked_urlopen.return_value = self.mock_response(b"<not-xml")
        with self.assertRaisesRegex(
            ABNLookupError, "The ABR service returned an unexpected response"
        ):
            lookup_by_abn(VALID_ABN, authentication_guid="test-guid")


if __name__ == "__main__":
    unittest.main()
