import pytest
from odata_json import Edm, EdmType, EdmTypeCode, OData


class TestOData:
    """Tests for OData class."""

    def test_version_constants(self):
        """Test OData version constants."""
        assert OData.V2 == 2
        assert OData.V4 == 4
        assert OData.V4_01 == 401

    def test_text_property_v2(self):
        """Test text property for V2."""
        odata = OData(OData.V2)
        assert odata.text == "2.0"

    def test_text_property_v4(self):
        """Test text property for V4."""
        odata = OData(OData.V4)
        assert odata.text == "4.0"

    def test_text_property_v4_01(self):
        """Test text property for V4.01."""
        odata = OData(OData.V4_01)
        assert odata.text == "4.01"

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
        """Test path_value with string type."""
        odata = OData(OData.V4)
        result = odata.path_value("test", Edm.String)
        assert result == "'test'"

    def test_path_value_binary(self):
        """Test path_value with binary type."""
        odata = OData(OData.V4)
        result = odata.path_value(b"hello", Edm.Binary)
        assert result.startswith("binary'")
        assert result.endswith("'")

    def test_path_value_binary_invalid_type(self):
        """Test path_value with binary type and invalid data."""
        odata = OData(OData.V4)
        with pytest.raises(ValueError, match="Expected bytes or bytearray"):
            odata.path_value("not bytes", Edm.Binary)

    def test_path_value_enum(self):
        """Test path_value with enum type."""
        odata = OData(OData.V4)
        enum_type = Edm.Enum("Status", EdmTypeCode.Enum)
        result = odata.path_value("Active", enum_type)
        assert "'" in result

    def test_path_value_number(self):
        """Test path_value with number type."""
        odata = OData(OData.V4)
        result = odata.path_value(42, Edm.Int32)
        assert result == "42"

    def test_body_value_string(self):
        """Test body_value with string type."""
        odata = OData(OData.V4)
        result = odata.body_value("test", Edm.String)
        assert result == "test"

    def test_body_value_number(self):
        """Test body_value with number type."""
        odata = OData(OData.V4)
        result = odata.body_value(42, Edm.Int32)
        assert result == 42

    def test_body_value_binary(self):
        """Test body_value with binary type."""
        odata = OData(OData.V4)
        result = odata.body_value(b"hello", Edm.Binary)
        assert result == "aGVsbG8"

    def test_body_value_binary_invalid_type(self):
        """Test body_value with binary type and invalid data."""
        odata = OData(OData.V4)
        with pytest.raises(ValueError, match="Expected bytes or bytearray"):
            odata.body_value("not bytes", Edm.Binary)

    def test_body_value_enum(self):
        """Test body_value with enum type."""
        odata = OData(OData.V4)
        enum_type = Edm.Enum("Status", EdmTypeCode.Enum)
        result = odata.body_value("Active", enum_type)
        assert "'" in result
