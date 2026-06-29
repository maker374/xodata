# Copyright (c) 2026 maker374
# https://github.com/maker374/xodata

from enum import Enum, auto
from requests import Request
from typing import Any
from urllib.parse import quote
import base64

class EdmTypeCode(Enum):
    Binary = auto()
    Boolean = auto()
    Byte = auto()
    Date = auto()
    DateTime = auto()
    DateTimeOffset = auto()
    Decimal = auto()
    Double = auto()
    Duration = auto()
    Enum = auto()  # pseudo-type code
    Geography = auto()
    GeographyPoint = auto()
    GeographyLineString = auto()
    GeographyPolygon = auto()
    GeographyMultiPoint = auto()
    GeographyMultiLineString = auto()
    GeographyMultiPolygon = auto()
    GeographyCollection = auto()
    Geometry = auto()
    GeometryPoint = auto()
    GeometryLineString = auto()
    GeometryPolygon = auto()
    GeometryMultiPoint = auto()
    GeometryMultiLineString = auto()
    GeometryMultiPolygon = auto()
    GeometryCollection = auto()
    Guid = auto()
    Int16 = auto()
    Int32 = auto()
    Int64 = auto()
    SByte = auto()
    Single = auto()
    Stream = auto()
    String = auto()
    TimeOfDay = auto()

class EdmType:
    def __init__(
        self,
        code: EdmTypeCode,
        name: str | None = None,
        nullable: bool = True,
        max_length: int | None = None,
        precision: int | None = None,
        scale: int | None = None,
    ) -> None:
        self.code = code
        self.name = name
        self.nullable = nullable
        self.max_length = max_length
        self.precision = precision
        self.scale = scale

    @property
    def is_binary(self) -> bool:
        return self.code == EdmTypeCode.Binary

    @property
    def is_string(self) -> bool:
        return self.code == EdmTypeCode.String

    @property
    def is_number(self) -> bool:
        return self.code in {
            EdmTypeCode.Byte,
            EdmTypeCode.Decimal,
            EdmTypeCode.Double,
            EdmTypeCode.Int16,
            EdmTypeCode.Int32,
            EdmTypeCode.Int64,
            EdmTypeCode.SByte,
            EdmTypeCode.Single,
        }
    
    @property
    def is_enum(self) -> bool:
        return self.code == EdmTypeCode.Enum

    def __repr__(self) -> str:
        if (self.name):
            return self.name
        return str(self.code)

class Edm:
    Binary = EdmType(EdmTypeCode.Binary)
    Boolean = EdmType(EdmTypeCode.Boolean)
    Byte = EdmType(EdmTypeCode.Byte)
    Date = EdmType(EdmTypeCode.Date)
    DateTime = EdmType(EdmTypeCode.DateTime)
    DateTimeOffset = EdmType(EdmTypeCode.DateTimeOffset)
    Decimal = EdmType(EdmTypeCode.Decimal)
    Double = EdmType(EdmTypeCode.Double)
    Duration = EdmType(EdmTypeCode.Duration)
    Geography = EdmType(EdmTypeCode.Geography)
    GeographyPoint = EdmType(EdmTypeCode.GeographyPoint)
    GeographyLineString = EdmType(EdmTypeCode.GeographyLineString)
    GeographyPolygon = EdmType(EdmTypeCode.GeographyPolygon)
    GeographyMultiPoint = EdmType(EdmTypeCode.GeographyMultiPoint)
    GeographyMultiLineString = EdmType(EdmTypeCode.GeographyMultiLineString)
    GeographyMultiPolygon = EdmType(EdmTypeCode.GeographyMultiPolygon)
    GeographyCollection = EdmType(EdmTypeCode.GeographyCollection)
    Geometry = EdmType(EdmTypeCode.Geometry)
    GeometryPoint = EdmType(EdmTypeCode.GeometryPoint)
    GeometryLineString = EdmType(EdmTypeCode.GeometryLineString)
    GeometryPolygon = EdmType(EdmTypeCode.GeometryPolygon)
    GeometryMultiPoint = EdmType(EdmTypeCode.GeometryMultiPoint)
    GeometryMultiLineString = EdmType(EdmTypeCode.GeometryMultiLineString)
    GeometryMultiPolygon = EdmType(EdmTypeCode.GeometryMultiPolygon)
    GeometryCollection = EdmType(EdmTypeCode.GeometryCollection)
    Guid = EdmType(EdmTypeCode.Guid)
    Int16 = EdmType(EdmTypeCode.Int16)
    Int32 = EdmType(EdmTypeCode.Int32)
    Int64 = EdmType(EdmTypeCode.Int64)
    SByte = EdmType(EdmTypeCode.SByte)
    Single = EdmType(EdmTypeCode.Single)
    Stream = EdmType(EdmTypeCode.Stream)
    String = EdmType(EdmTypeCode.String)
    TimeOfDay = EdmType(EdmTypeCode.TimeOfDay)

    @classmethod
    def Enum(cls, name: str, code: EdmTypeCode) -> EdmType:
        return EdmType(EdmTypeCode.Enum, name=name)

class ODataProperty:
    pass

class ODataResource:
    pass

class OData:
    """Conversion of Python data to OData JSON format."""

    V2 = 200
    V4 = 400
    V4_01 = 401

    def __init__(self, version: int) -> None:
        self._version = version

    @property
    def version_text(self) -> str:
        version = self._version
        if version == OData.V2:
            return "2.0"
        if version == OData.V4:
            return "4.0"
        if version == OData.V4_01:
            return "4.01"
        raise ValueError(f"Unsupported OData version: {self._version}")

    @property
    def at_type(self) -> str:
        if self._version == OData.V4_01:
            return "@type"
        return "@odata.type"
    
    def add_http_headers(self, request: Request) -> None:
        self._check_version()
        for header in ["OData-Version", "OData-MaxVersion"]:
            request.headers[header] = self.version_text
        method = request.method.upper()
        if method in ["POST", "PUT", "PATCH"]:
            request.headers["Content-Type"] = "application/json;odata.metadata=minimal"

    def resource(self, name: str) -> ODataResource:
        return ODataResource(self, name)
    
    def property(self, name: str, type: EdmType) -> ODataProperty:
        return ODataProperty(self, name, type)
    
    def entity_with_key(self, entity_set: str, entity_key: list[tuple[str, Any, EdmType]]) -> str:
        self._check_version()
        version = self._version
        entity_set_encoded = self.percent_encode(entity_set)
        if version < OData.V4 or len(entity_key) != 1:
            # e.g. V2 or multiple keys: use name=value pairs
            key_values = [f"{key_name}={self.value_in_path(key_value, key_type)}" for key_name, key_value, key_type in entity_key]
        else:
            key_values = [self.value_in_path(key_value, key_type) for _, key_value, key_type in entity_key]
        return f"{entity_set_encoded}({','.join(key_values)})"

    def value_in_key(self, value: Any, type: EdmType) -> tuple[str, Any, EdmType]:
        return (self.value_in_path(value, type), value, type)

    def value_in_path(self, value: Any, type: EdmType) -> Any:
        # TODO: V2/V4 differences
        self._check_version()
        if type.is_string:
            return self.quoted_string(value)
        if type.is_binary:
            if isinstance(value, (bytes, bytearray)):
                return f"binary'{self.to_base64url(value)}'"
            raise ValueError(f"Expected bytes or bytearray for binary type, got {str(type)}")
        if type.is_enum:
            return f"{type.name}'{str(value)}'"
        return str(value)

    def value_in_body(self, value: Any, type: EdmType) -> Any:
        # TODO: V2/V4 differences
        if value is None:
            return None
        self._check_version()
        if type.is_number or type.is_string:
            return value
        if type.is_binary:
            if isinstance(value, (bytes, bytearray)):
                return self.to_base64url(value)
            raise ValueError(f"Expected bytes or bytearray for binary type, got {str(type)}")
        if type.is_enum:
            return f"{type.name}'{str(value)}'"
        return str(value)
    
    def _check_version(self) -> None:
        version = self._version
        if version == OData.V2:
            raise NotImplementedError("OData V2 is not supported yet")

    def percent_encode(self, value: Any) -> str:
        return quote(str(value), safe="'+-._~")

    def percent_encode_in_string(self, value: Any) -> str:
        return quote(str(value), safe="'")

    def quoted_string(self, value: Any) -> str:
        encoded = self.percent_encode_in_string(value.replace('\'', '\'\''))
        return f"'{encoded}'"
    
    def to_base64url(self, data: bytes | bytearray) -> str:
        return base64.urlsafe_b64encode(bytes(data)).decode("ascii").rstrip("=")

class ODataProperty:
    def __init__(self, odata: OData, name: str, type: EdmType) -> None:
        self.odata = odata
        self.name = name
        self.type = type

    def body_value(self, value: Any) -> tuple[str, Any]:
        return (self.name, self.odata.value_in_body(value, self.type))
    
    def key_value(self, value: Any) -> tuple[str, Any, EdmType]:
        return (self.name, value, self.type)

class ODataResource:
    def __init__(self, odata: OData, name: str) -> None:
        self.odata = odata
        self.name = name
    
    def with_key(self, entity_key: list[tuple[str, Any, EdmType]]) -> str:
        return self.odata.entity_with_key(self.name, entity_key)
