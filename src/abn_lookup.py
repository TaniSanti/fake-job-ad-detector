"""ABN Lookup Document Style Web Service integration.

Credentials are supplied at runtime and are never written to logs or returned
in user-facing errors. The service response is evidence about ABR records only.
"""
from difflib import SequenceMatcher
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ABN_SEARCH_ENDPOINT = (
    "https://abr.business.gov.au/ABRXMLSearch/"
    "AbrXmlSearch.asmx/SearchByABNv202001"
)
NAME_SEARCH_ENDPOINT = (
    "https://abr.business.gov.au/ABRXMLSearch/"
    "AbrXmlSearch.asmx/ABRSearchByNameAdvancedSimpleProtocol2017"
)
REQUEST_TIMEOUT_SECONDS = 10


class ABNLookupError(Exception):
    """Safe, user-displayable failure from validation or ABR lookup."""


class MissingCredentialsError(ABNLookupError):
    """The ABR authentication GUID has not been configured."""


def get_authentication_guid(secrets=None):
    """Get the GUID from the environment, then Streamlit Secrets if provided."""
    guid = os.getenv("ABR_AUTHENTICATION_GUID")
    if not guid and secrets is not None:
        try:
            guid = secrets.get("ABR_AUTHENTICATION_GUID")
        except Exception:
            guid = None
    if not guid or not str(guid).strip():
        raise MissingCredentialsError(
            "ABN Lookup is not configured. Set ABR_AUTHENTICATION_GUID "
            "in your environment or Streamlit Secrets."
        )
    return str(guid).strip()


def normalize_abn(value):
    """Remove common spaces/hyphens and return digits, or an empty string."""
    return re.sub(r"[\s-]", "", str(value or ""))


def is_valid_abn(value):
    """Validate the 11 digit ABN format and official checksum algorithm."""
    digits = normalize_abn(value)
    if not digits.isdigit() or len(digits) != 11:
        return False

    weights = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
    total = (int(digits[0]) - 1) * weights[0]
    total += sum(int(digit) * weight for digit, weight in zip(digits[1:], weights[1:]))
    return total % 89 == 0


def extract_abn(text):
    """Extract the first 11-digit ABN candidate, allowing spaces or hyphens."""
    candidate_pattern = re.compile(r"(?<!\d)(?:\d[\s-]?){10}\d(?!\d)")
    for match in candidate_pattern.finditer(text or ""):
        candidate = normalize_abn(match.group())
        if is_valid_abn(candidate):
            return candidate
    return ""


def compare_entity_name(supplied_name, returned_name):
    """Return a cautious text comparison; it cannot verify who posted an ad."""
    supplied = re.sub(r"[^a-z0-9]+", " ", (supplied_name or "").lower()).strip()
    returned = re.sub(r"[^a-z0-9]+", " ", (returned_name or "").lower()).strip()
    if not supplied or not returned:
        return {"status": "unavailable", "similarity": None}

    ratio = SequenceMatcher(None, supplied, returned).ratio()
    if supplied == returned:
        status = "exact"
    elif supplied in returned or returned in supplied or ratio >= 0.8:
        status = "similar"
    else:
        status = "different"
    return {"status": status, "similarity": ratio}


def _local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _find_text(node, names):
    accepted = {name.lower() for name in names}
    for element in node.iter():
        if _local_name(element.tag) in accepted and element.text:
            value = element.text.strip()
            if value:
                return value
    return ""


def _find_group(node, names):
    accepted = {name.lower() for name in names}
    for element in node.iter():
        if _local_name(element.tag) in accepted:
            return element
    return None


def _check_service_exception(root):
    code = _find_text(root, {"exceptionCode"})
    description = _find_text(root, {"exceptionDescription"})
    if not code and not description:
        return
    safe_description = description.lower()
    if code.upper() == "SEARCH" or "no records found" in safe_description:
        raise ABNLookupError("No matching ABR record was found.")
    # Do not echo the server response: it may contain request details.
    raise ABNLookupError(
        "The ABR service could not complete this search. "
        "Check the details or try again later."
    )


def _post_form(endpoint, parameters, authentication_guid):
    fields = dict(parameters)
    fields["authenticationGuid"] = authentication_guid
    request = Request(
        endpoint,
        data=urlencode(fields).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/xml",
            "User-Agent": "FakeJobAdvertisementDetector/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except HTTPError as error:
        if error.code == 404:
            raise ABNLookupError("The ABR service endpoint was not found.") from None
        raise ABNLookupError(
            "The ABR service returned an error. Please try again later."
        ) from None
    except (URLError, TimeoutError, OSError):
        raise ABNLookupError(
            "Could not connect to the ABR service. Check your connection and try again."
        ) from None

    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise ABNLookupError(
            "The ABR service returned an unexpected response."
        ) from None
    _check_service_exception(root)
    return root


def _parse_entity(node):
    abn = _find_text(node, {"identifierValue"})
    status = _find_text(node, {"entityStatusCode"})
    entity_name = _find_text(node, {"organisationName"})
    if not entity_name:
        given = _find_text(node, {"givenName"})
        other = _find_text(node, {"otherGivenName"})
        family = _find_text(node, {"familyName"})
        entity_name = " ".join(part for part in (given, other, family) if part)

    entity_type = _find_text(node, {"entityDescription"})
    state = _find_text(node, {"stateCode"})
    gst_group = _find_group(node, {"goodsAndServicesTax"})
    gst_status = "Registered" if gst_group is not None else "Not shown as registered"
    gst_from = _find_text(gst_group, {"effectiveFrom"}) if gst_group is not None else ""

    return {
        "abn": abn,
        "entity_name": entity_name,
        "status": status,
        "entity_type": entity_type,
        "gst_status": gst_status,
        "gst_from": gst_from,
        "state": state,
        "registration_date": _find_text(node, {"registrationDate"}),
    }


def lookup_by_abn(abn, authentication_guid=None, secrets=None):
    """Look up a checksum-valid ABN with the current Document Style method."""
    normalized = normalize_abn(abn)
    if not is_valid_abn(normalized):
        raise ABNLookupError("Enter a valid 11-digit ABN.")
    guid = authentication_guid or get_authentication_guid(secrets)
    root = _post_form(
        ABN_SEARCH_ENDPOINT,
        {
            "searchString": normalized,
            "includeHistoricalDetails": "N",
        },
        guid,
    )
    entity_node = _find_group(root, {"businessEntity", "businessEntity202001"})
    if entity_node is None:
        raise ABNLookupError("The ABR service returned an unexpected response.")
    entity = _parse_entity(entity_node)
    entity["abn"] = entity["abn"] or normalized
    return entity


def search_by_name(name, authentication_guid=None, secrets=None):
    """Search official legal and registered business names; return candidates."""
    query = (name or "").strip()
    if len(query) < 2:
        raise ABNLookupError("Enter a business name with at least two characters.")
    if re.fullmatch(r"[\d\s-]+", query):
        raise ABNLookupError("Enter a company name here, not an ABN.")
    guid = authentication_guid or get_authentication_guid(secrets)

    parameters = {
        "name": query,
        "postcode": "",
        "legalName": "Y",
        "tradingName": "N",
        "businessName": "Y",
        "activeABNsOnly": "N",
        "NSW": "", "SA": "", "ACT": "", "VIC": "",
        "WA": "", "NT": "", "QLD": "", "TAS": "",
        "searchWidth": "Typical",
        "minimumScore": "80",
        "maxSearchResults": "10",
    }
    root = _post_form(NAME_SEARCH_ENDPOINT, parameters, guid)

    candidates = []
    seen = set()
    record_names = {"searchresultsrecord", "searchresult", "matchingname"}
    for node in root.iter():
        if _local_name(node.tag) not in record_names:
            continue
        abn = normalize_abn(_find_text(node, {"identifierValue", "abn"}))
        if len(abn) != 11 or not abn.isdigit() or abn in seen:
            continue
        seen.add(abn)
        candidates.append({
            "abn": abn,
            "entity_name": _find_text(
                node, {"organisationName", "mainName", "matchingName", "name"}
            ),
            "status": _find_text(node, {"entityStatusCode", "abnStatus"}),
            "state": _find_text(node, {"stateCode"}),
            "match_score": _find_text(node, {"matchScore"}),
        })

    # Some response versions nest record fields without a named record node.
    if not candidates:
        for node in root.iter():
            if _local_name(node.tag) not in {"response", "searchresultslist"}:
                continue
            for child in node:
                abn = normalize_abn(_find_text(child, {"identifierValue", "abn"}))
                if len(abn) != 11 or not abn.isdigit() or abn in seen:
                    continue
                seen.add(abn)
                candidates.append({
                    "abn": abn,
                    "entity_name": _find_text(
                        child, {"organisationName", "mainName", "matchingName", "name"}
                    ),
                    "status": _find_text(child, {"entityStatusCode", "abnStatus"}),
                    "state": _find_text(child, {"stateCode"}),
                    "match_score": _find_text(child, {"matchScore"}),
                })
    return candidates
