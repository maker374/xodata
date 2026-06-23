# Copyright (c) 2026 maker374
# https://github.com/maker374

from enum import Enum, IntEnum, auto
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

class ODataVersion(IntEnum):
    """OData protocol versions."""

    V2 = 2
    V4 = 4
    V4_01 = 401

class OData:
    """Conversion of Python data to OData JSON format."""

    V2 = 2
    V4 = 4
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

    def path_value(self, value: Any, type: EdmType) -> Any:
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

    def body_value(self, value: Any, type: EdmType) -> Any:
        # TODO: V2/V4 differences
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
