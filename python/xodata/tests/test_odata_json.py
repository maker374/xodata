import pytest
from odata_json import Edm, EdmType, EdmTypeCode, OData


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

    def test_v2_not_implemented(self):
        """Test that V2 raises NotImplementedError."""
        odata = OData(OData.V2)
        with pytest.raises(NotImplementedError, match="OData V2 is not supported yet"):
            odata.add_http_headers(None)

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
