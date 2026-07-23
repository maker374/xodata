import base64
import math
import uuid
from datetime import datetime, date, time, timezone, timedelta
from decimal import Decimal

import pytest
from odata_json import Edm, EdmType, EdmTypeCode, OData, ODataProperty, ODataResource


class MockRequest:
    """Minimal stand-in for requests.Request used in add_http_headers tests."""

    def __init__(self, method: str) -> None:
        self.method = method
        self.headers: dict = {}


class TestOData:
    """Tests for OData class."""

    def test_version_constants(self):
        """Test OData version constants."""
        assert OData.V2 == 200
        assert OData.V4 == 400
        assert OData.V4_01 == 401

    def test_version_text_property_v2(self):
        """Test version_text property for V2."""
        odata = OData(OData.V2)
        assert odata.version_text == "2.0"

    def test_version_text_property_v4(self):
        """Test version_text property for V4."""
        odata = OData(OData.V4)
        assert odata.version_text == "4.0"

    def test_version_text_property_v4_01(self):
        """Test version_text property for V4.01."""
        odata = OData(OData.V4_01)
        assert odata.version_text == "4.01"

    def test_init(self):
        """Test OData initialization."""
        odata = OData(OData.V4)
        assert odata._version == OData.V4

    def test_at_type_property_v4(self):
        """Test at_type property for V4."""
        odata = OData(OData.V4)
        assert odata.at_type == "@odata.type"

    def test_at_type_property_v4_01(self):
        """Test at_type property for V4.01."""
        odata = OData(OData.V4_01)
        assert odata.at_type == "@type"

    def test_v2_uses_dataservice_headers(self):
        """Test that V2 uses DataServiceVersion headers."""
        odata = OData(OData.V2)
        req = MockRequest("GET")
        odata.add_http_headers(req)
        assert "DataServiceVersion" in req.headers
        assert "MaxDataServiceVersion" in req.headers

    def test_quoted_string(self):
        """Test quoted_string method."""
        odata = OData(OData.V4)
        result = odata.quoted_string("hello")
        assert result == "'hello'"

    def test_quoted_string_with_quotes(self):
        """Test quoted_string method with single quotes in value."""
        odata = OData(OData.V4)
        result = odata.quoted_string("it's")
        assert result == "'it''s'"

    def test_percent_encode(self):
        """Test percent_encode method."""
        odata = OData(OData.V4)
        result = odata.percent_encode("hello world")
        assert result == "hello%20world"

    def test_percent_encode_special_chars(self):
        """Test percent_encode method with special characters."""
        odata = OData(OData.V4)
        result = odata.percent_encode("test@email.com")
        assert result == "test%40email.com"

    def test_to_base64url(self):
        """Test to_base64url method."""
        odata = OData(OData.V4)
        data = b"hello"
        result = odata.to_base64url(data)
        assert result == "aGVsbG8"

    def test_to_base64url_with_padding(self):
        """Test to_base64url method strips padding."""
        odata = OData(OData.V4)
        data = b"hi"
        result = odata.to_base64url(data)
        # Standard base64 would be "aGk=" but to_base64url strips the "="
        assert "=" not in result

    def test_path_value_string(self):
        """Test value_in_path with string type."""
        odata = OData(OData.V4)
        result = odata.value_in_path("test", Edm.String)
        assert result == "'test'"

    def test_path_value_binary(self):
        """Test value_in_path with binary type."""
        odata = OData(OData.V4)
        result = odata.value_in_path(b"hello", Edm.Binary)
        assert result.startswith("binary'")
        assert result.endswith("'")

    def test_path_value_binary_invalid_type(self):
        """Test value_in_path with binary type and invalid data."""
        odata = OData(OData.V4)
        with pytest.raises(ValueError, match="Expected bytes or bytearray"):
            odata.value_in_path("not bytes", Edm.Binary)

    def test_path_value_enum(self):
        """Test value_in_path with enum type."""
        odata = OData(OData.V4)
        enum_type = Edm.Enum("Status", EdmTypeCode.Enum)
        result = odata.value_in_path("Active", enum_type)
        assert "'" in result

    def test_path_value_number(self):
        """Test value_in_path with number type."""
        odata = OData(OData.V4)
        result = odata.value_in_path(42, Edm.Int32)
        assert result == "42"

    def test_body_value_string(self):
        """Test value_in_body with string type."""
        odata = OData(OData.V4)
        result = odata.value_in_body("test", Edm.String)
        assert result == "test"

    def test_body_value_number(self):
        """Test value_in_body with number type."""
        odata = OData(OData.V4)
        result = odata.value_in_body(42, Edm.Int32)
        assert result == 42

    def test_body_value_binary(self):
        """Test value_in_body with binary type."""
        odata = OData(OData.V4)
        result = odata.value_in_body(b"hello", Edm.Binary)
        assert result == "aGVsbG8"

    def test_body_value_binary_invalid_type(self):
        """Test value_in_body with binary type and invalid data."""
        odata = OData(OData.V4)
        with pytest.raises(ValueError, match="Expected bytes or bytearray"):
            odata.value_in_body("not bytes", Edm.Binary)

    def test_body_value_enum(self):
        """Test value_in_body with enum type."""
        odata = OData(OData.V4)
        enum_type = Edm.Enum("Status", EdmTypeCode.Enum)
        result = odata.value_in_body("Active", enum_type)
        assert "'" in result


class TestEdmType:
    def test_is_binary_true(self):
        assert Edm.Binary.is_binary is True

    def test_is_binary_false(self):
        assert Edm.String.is_binary is False

    def test_is_string_true(self):
        assert Edm.String.is_string is True

    def test_is_string_false(self):
        assert Edm.Int32.is_string is False

    def test_is_number_true(self):
        for t in [Edm.Byte, Edm.Decimal, Edm.Double, Edm.Int16, Edm.Int32, Edm.Int64, Edm.SByte, Edm.Single]:
            assert t.is_number is True

    def test_is_number_false(self):
        assert Edm.String.is_number is False

    def test_is_enum_true(self):
        assert Edm.Enum("Status", EdmTypeCode.Enum).is_enum is True

    def test_is_enum_false(self):
        assert Edm.Int32.is_enum is False

    def test_is_guid_true(self):
        assert Edm.Guid.is_guid is True

    def test_is_guid_false(self):
        assert Edm.String.is_guid is False

    def test_repr_with_name(self):
        t = EdmType(EdmTypeCode.String, name="MyCustomType")
        assert repr(t) == "MyCustomType"

    def test_repr_without_name(self):
        t = EdmType(EdmTypeCode.Int32)
        assert "Int32" in repr(t)


class TestODataVersionText:
    def test_version_text_unsupported_raises(self):
        odata = OData(999)
        with pytest.raises(ValueError, match="Unsupported OData version"):
            _ = odata.version_text


class TestODataAtType:
    def test_at_type_v2(self):
        odata = OData(OData.V2)
        assert odata.at_type == "@odata.type"


class TestODataAddHttpHeaders:
    def test_get_sets_odata_version_headers(self):
        odata = OData(OData.V4)
        req = MockRequest("GET")
        odata.add_http_headers(req)
        assert req.headers["OData-Version"] == "4.0"
        assert req.headers["OData-MaxVersion"] == "4.0"

    def test_get_sets_accept_not_content_type(self):
        odata = OData(OData.V4)
        req = MockRequest("GET")
        odata.add_http_headers(req)
        assert "application/json" in req.headers["Accept"]
        assert "Content-Type" not in req.headers

    def test_delete_sets_no_accept_no_content_type(self):
        odata = OData(OData.V4)
        req = MockRequest("DELETE")
        odata.add_http_headers(req)
        assert "Accept" not in req.headers
        assert "Content-Type" not in req.headers

    def test_post_sets_content_type_and_accept(self):
        odata = OData(OData.V4)
        req = MockRequest("POST")
        odata.add_http_headers(req)
        assert "application/json" in req.headers["Content-Type"]
        assert "application/json" in req.headers["Accept"]

    def test_put_sets_content_type(self):
        odata = OData(OData.V4)
        req = MockRequest("PUT")
        odata.add_http_headers(req)
        assert "Content-Type" in req.headers

    def test_patch_sets_content_type(self):
        odata = OData(OData.V4)
        req = MockRequest("PATCH")
        odata.add_http_headers(req)
        assert "Content-Type" in req.headers

    def test_v4_01_version_in_header(self):
        odata = OData(OData.V4_01)
        req = MockRequest("GET")
        odata.add_http_headers(req)
        assert req.headers["OData-Version"] == "4.01"

    def test_metadata_minimal_in_accept(self):
        odata = OData(OData.V4)
        req = MockRequest("GET")
        odata.add_http_headers(req)
        assert "odata.metadata=minimal" in req.headers["Accept"]


class TestODataValueInPathExtended:
    def test_null_returns_null_string(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(None, Edm.String) == "null"

    def test_boolean_true(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(True, Edm.Boolean) == "true"

    def test_boolean_false(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(False, Edm.Boolean) == "false"

    def test_guid_v4(self):
        odata = OData(OData.V4)
        g = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert odata.value_in_path(g, Edm.Guid) == str(g)

    def test_guid_v2_has_prefix(self):
        odata = OData(OData.V2)
        g = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = odata.value_in_path(g, Edm.Guid)
        assert result == f"guid'{g}'"

    def test_date_v4(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(date(2024, 3, 15), Edm.Date) == "2024-03-15"

    def test_date_v2_has_prefix(self):
        odata = OData(OData.V2)
        result = odata.value_in_path(date(2024, 3, 15), Edm.Date)
        assert result == "date'2024-03-15'"

    def test_datetime_v4_contains_date(self):
        odata = OData(OData.V4)
        result = odata.value_in_path(datetime(2024, 3, 15, 10, 30, 0), Edm.DateTime)
        assert "2024-03-15" in result

    def test_datetime_v2_has_prefix(self):
        odata = OData(OData.V2)
        result = odata.value_in_path(datetime(2024, 3, 15, 10, 30, 0), Edm.DateTime)
        assert result.startswith("datetime'")

    def test_datetimeoffset_v2_has_prefix(self):
        odata = OData(OData.V2)
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = odata.value_in_path(dt, Edm.DateTimeOffset)
        assert result.startswith("datetimeoffset'")

    def test_int64_v2_suffix_L(self):
        odata = OData(OData.V2)
        assert odata.value_in_path(100, Edm.Int64).endswith("L")

    def test_decimal_v2_suffix_M(self):
        odata = OData(OData.V2)
        assert odata.value_in_path(Decimal("3.14"), Edm.Decimal).endswith("M")

    def test_single_v2_suffix_F(self):
        odata = OData(OData.V2)
        assert odata.value_in_path(3.14, Edm.Single).endswith("F")

    def test_double_v2_suffix_D(self):
        odata = OData(OData.V2)
        assert odata.value_in_path(3.14, Edm.Double).endswith("D")

    def test_decimal_v4_no_suffix(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(Decimal("3.14"), Edm.Decimal) == "3.14"

    def test_nan_double(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(float("nan"), Edm.Double) == "NaN"

    def test_inf_double(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(float("inf"), Edm.Double) == "INF"

    def test_neg_inf_double(self):
        odata = OData(OData.V4)
        assert odata.value_in_path(float("-inf"), Edm.Double) == "-INF"

    def test_nan_single_v2_suffix(self):
        odata = OData(OData.V2)
        result = odata.value_in_path(float("nan"), Edm.Single)
        assert result == "NaNF"

    def test_binary_v2_hex_format(self):
        odata = OData(OData.V2)
        result = odata.value_in_path(b"\xde\xad\xbe\xef", Edm.Binary)
        assert result == "X'DEADBEEF'"

    def test_timeofday_v4_contains_time(self):
        odata = OData(OData.V4)
        result = odata.value_in_path(time(10, 30, 0), Edm.TimeOfDay)
        assert "10" in result and "30" in result

    def test_duration_v4_contains_seconds(self):
        odata = OData(OData.V4)
        result = odata.value_in_path(3600, Edm.Duration)
        assert "3600" in result

    def test_time_v2_has_prefix(self):
        odata = OData(OData.V2)
        result = odata.value_in_path(60, Edm.Time)
        assert result.startswith("time'")


class TestODataValueInBodyExtended:
    def test_null_returns_none(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(None, Edm.String) is None

    def test_boolean_true(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(True, Edm.Boolean) == "true"

    def test_boolean_false(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(False, Edm.Boolean) == "false"

    def test_date_from_date_object(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(date(2024, 3, 15), Edm.Date) == "2024-03-15"

    def test_date_from_datetime_object(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(datetime(2024, 3, 15, 10, 0), Edm.Date) == "2024-03-15"

    def test_date_from_iso_string(self):
        odata = OData(OData.V4)
        assert odata.value_in_body("2024-03-15", Edm.Date) == "2024-03-15"

    def test_datetime_without_tz(self):
        odata = OData(OData.V4)
        result = odata.value_in_body(datetime(2024, 3, 15, 10, 30, 0), Edm.DateTime)
        assert result == "2024-03-15T10:30:00"

    def test_datetime_with_tz_raises(self):
        odata = OData(OData.V4)
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="must not have zone offset"):
            odata.value_in_body(dt, Edm.DateTime)

    def test_datetimeoffset_with_utc(self):
        odata = OData(OData.V4)
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = odata.value_in_body(dt, Edm.DateTimeOffset)
        assert "2024-03-15" in result

    def test_datetimeoffset_without_tz_appends_z(self):
        odata = OData(OData.V4)
        dt = datetime(2024, 3, 15, 10, 30, 0)
        result = odata.value_in_body(dt, Edm.DateTimeOffset)
        assert result.endswith("Z")

    def test_duration_from_int(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(3600, Edm.Duration) == "PT3600S"

    def test_duration_from_decimal(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(Decimal("90.5"), Edm.Duration) == "PT90.5S"

    def test_duration_from_float(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(1.5, Edm.Duration) == "PT1.5S"

    def test_duration_from_string_passthrough(self):
        odata = OData(OData.V4)
        assert odata.value_in_body("PT1H", Edm.Duration) == "PT1H"

    def test_guid_from_uuid_object(self):
        odata = OData(OData.V4)
        g = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert odata.value_in_body(g, Edm.Guid) == str(g)

    def test_guid_from_string(self):
        odata = OData(OData.V4)
        result = odata.value_in_body("12345678-1234-5678-1234-567812345678", Edm.Guid)
        assert result == "12345678-1234-5678-1234-567812345678"

    def test_guid_from_hex_string_32_chars(self):
        odata = OData(OData.V4)
        result = odata.value_in_body("12345678123456781234567812345678", Edm.Guid)
        assert "-" in result

    def test_guid_from_bytes(self):
        odata = OData(OData.V4)
        g = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert odata.value_in_body(g.bytes, Edm.Guid) == str(g)

    def test_binary_v4_base64url(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(b"hello", Edm.Binary) == "aGVsbG8"

    def test_binary_v2_standard_base64(self):
        odata = OData(OData.V2)
        result = odata.value_in_body(b"hello", Edm.Binary)
        assert result == base64.b64encode(b"hello").decode("ascii")

    def test_number_v4_returns_as_is(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(42, Edm.Int32) == 42

    def test_number_v2_int32_returns_int(self):
        odata = OData(OData.V2)
        assert odata.value_in_body(42, Edm.Int32) == 42

    def test_number_v2_int64_returns_string(self):
        odata = OData(OData.V2)
        assert odata.value_in_body(42, Edm.Int64) == "42"

    def test_nan_in_body(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(float("nan"), Edm.Double) == "NaN"

    def test_inf_in_body(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(float("inf"), Edm.Double) == "INF"

    def test_neg_inf_in_body(self):
        odata = OData(OData.V4)
        assert odata.value_in_body(float("-inf"), Edm.Double) == "-INF"


class TestODataEntityWithKey:
    def test_single_key_v4_no_name(self):
        odata = OData(OData.V4)
        result = odata.entity_with_key("Orders", [("Id", 42, Edm.Int32)])
        assert result == "Orders(42)"

    def test_single_string_key_v4(self):
        odata = OData(OData.V4)
        result = odata.entity_with_key("Items", [("Code", "abc", Edm.String)])
        assert result == "Items('abc')"

    def test_multiple_keys_v4_uses_names(self):
        odata = OData(OData.V4)
        result = odata.entity_with_key("OrderItems", [("OrderId", 1, Edm.Int32), ("ItemId", 2, Edm.Int32)])
        assert "OrderId=1" in result
        assert "ItemId=2" in result
        assert result.startswith("OrderItems(")

    def test_single_key_v2_uses_name(self):
        odata = OData(OData.V2)
        result = odata.entity_with_key("Orders", [("Id", 42, Edm.Int32)])
        assert "Id=42" in result

    def test_entity_set_name_percent_encoded(self):
        odata = OData(OData.V4)
        result = odata.entity_with_key("My Orders", [("Id", 1, Edm.Int32)])
        assert "My%20Orders" in result


class TestODataValueInKey:
    def test_returns_path_value_original_type(self):
        odata = OData(OData.V4)
        path_str, raw, edm_type = odata.value_in_key(42, Edm.Int32)
        assert path_str == "42"
        assert raw == 42
        assert edm_type is Edm.Int32


class TestODataPercentEncodeVariants:
    def test_percent_encode_in_string_encodes_spaces(self):
        odata = OData(OData.V4)
        result = odata.percent_encode_in_string("hello world")
        assert result == "hello%20world"

    def test_percent_encode_plus_is_safe(self):
        odata = OData(OData.V4)
        assert odata.percent_encode("hello+world") == "hello+world"


class TestODataToBase64:
    def test_to_base64_has_padding(self):
        odata = OData(OData.V4)
        result = odata.to_base64(b"hi")
        assert result == base64.b64encode(b"hi").decode("ascii")
        assert "=" in result

    def test_to_base64_bytes(self):
        odata = OData(OData.V4)
        assert odata.to_base64(b"hello") == "aGVsbG8="


class TestODataVerifyPatch:
    def test_no_mismatches(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch({"name": "Alice"}, {"name": "Alice", "age": 30}, {"name": Edm.String})
        assert mismatches == []

    def test_value_mismatch(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch({"name": "Alice"}, {"name": "Bob"}, {"name": Edm.String})
        assert len(mismatches) == 1
        assert "name" in mismatches[0]

    def test_field_not_in_patch_is_skipped(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"name": "Alice"},
            {"name": "Alice", "age": 99},
            {"name": Edm.String, "age": Edm.Int32},
        )
        assert mismatches == []

    def test_field_missing_in_get_response(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch({"name": "Alice"}, {}, {"name": Edm.String})
        assert len(mismatches) == 1
        assert "not present" in mismatches[0]

    def test_datetimeoffset_z_vs_plus00(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"ts": "2024-03-15T10:30:00Z"},
            {"ts": "2024-03-15T10:30:00+00:00"},
            {"ts": Edm.DateTimeOffset},
        )
        assert mismatches == []

    def test_datetime_same_values(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"ts": "2024-03-15T10:30:00"},
            {"ts": "2024-03-15T10:30:00"},
            {"ts": Edm.DateTime},
        )
        assert mismatches == []

    def test_duration_pt1h_equals_pt3600s(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch({"dur": "PT1H"}, {"dur": "PT3600S"}, {"dur": Edm.Duration})
        assert mismatches == []

    def test_nested_path_match(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"address": {"city": "Dublin"}},
            {"address": {"city": "Dublin"}},
            {"address.city": Edm.String},
        )
        assert mismatches == []

    def test_nested_path_mismatch(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"address": {"city": "Dublin"}},
            {"address": {"city": "London"}},
            {"address.city": Edm.String},
        )
        assert len(mismatches) == 1

    def test_timeofday_normalization(self):
        odata = OData(OData.V4)
        mismatches = odata.verify_patch(
            {"t": "10:30:00"},
            {"t": "10:30:00.000"},
            {"t": Edm.TimeOfDay},
        )
        assert mismatches == []


class TestXsDurationSeconds:
    def _odata(self):
        return OData(OData.V4)

    def test_hours(self):
        assert self._odata()._xs_duration_seconds("PT1H") == Decimal(3600)

    def test_minutes(self):
        assert self._odata()._xs_duration_seconds("PT30M") == Decimal(1800)

    def test_seconds(self):
        assert self._odata()._xs_duration_seconds("PT45S") == Decimal(45)

    def test_days(self):
        assert self._odata()._xs_duration_seconds("P1D") == Decimal(86400)

    def test_combined_day_and_hour(self):
        assert self._odata()._xs_duration_seconds("P1DT1H") == Decimal(86400 + 3600)

    def test_negative(self):
        assert self._odata()._xs_duration_seconds("-PT1H") == Decimal(-3600)

    def test_fractional_seconds(self):
        assert self._odata()._xs_duration_seconds("PT1.5S") == Decimal("1.5")

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid xs:duration"):
            self._odata()._xs_duration_seconds("not-a-duration")


class TestODataProperty:
    def test_body_value_string(self):
        odata = OData(OData.V4)
        prop = ODataProperty(odata, "name", Edm.String)
        name, value = prop.body_value("Alice")
        assert name == "name"
        assert value == "Alice"

    def test_body_value_int(self):
        odata = OData(OData.V4)
        prop = ODataProperty(odata, "count", Edm.Int32)
        name, value = prop.body_value(7)
        assert name == "count"
        assert value == 7

    def test_key_value_returns_name_value_type(self):
        odata = OData(OData.V4)
        prop = ODataProperty(odata, "id", Edm.Int32)
        name, value, edm_type = prop.key_value(42)
        assert name == "id"
        assert value == 42
        assert edm_type is Edm.Int32


class TestODataResource:
    def test_with_key_single(self):
        odata = OData(OData.V4)
        resource = ODataResource(odata, "Orders")
        prop = ODataProperty(odata, "Id", Edm.Int32)
        assert resource.with_key([prop.key_value(42)]) == "Orders(42)"

    def test_with_key_multiple(self):
        odata = OData(OData.V4)
        resource = ODataResource(odata, "OrderItems")
        id_prop = ODataProperty(odata, "OrderId", Edm.Int32)
        item_prop = ODataProperty(odata, "ItemId", Edm.Int32)
        result = resource.with_key([id_prop.key_value(1), item_prop.key_value(2)])
        assert "OrderId=1" in result
        assert "ItemId=2" in result


class TestODataFactoryMethods:
    def test_resource_factory(self):
        odata = OData(OData.V4)
        res = odata.resource("Orders", OData.EntitySet)
        assert isinstance(res, ODataResource)
        assert res.name == "Orders"
        assert res.kind == OData.EntitySet

    def test_property_factory(self):
        odata = OData(OData.V4)
        prop = odata.property("name", Edm.String)
        assert isinstance(prop, ODataProperty)
        assert prop.name == "name"
        assert prop.type is Edm.String
