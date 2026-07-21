# Copyright (c) 2026 maker374
# https://github.com/maker374/xodata
# Apache License 2.0
# Updated 2024-07-23

from datetime import datetime, time
from decimal import Decimal
from enum import Enum, auto
from requests import Request
from typing import Any
from urllib.parse import quote
import base64
import re

_MISSING = object()  # sentinel for missing value

_DECIMAL_NEG_ONE = Decimal(-1)
_DECIMAL_ONE = Decimal(1)
_SECONDS_PER_DAY = Decimal(86400)
_SECONDS_PER_HOUR = Decimal(3600)
_SECONDS_PER_MINUTE = Decimal(60)

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

    EntitySet = "EntitySet"
    Singleton = "Singleton"

    _DAY_TIME_DURATION_PATTERN = re.compile(
        r"""
        ^
        (?P<sign>-)?
        P
        (?:(?P<days>\d+)D)?
        (?:
            T
            (?:(?P<hours>\d+)H)?
            (?:(?P<minutes>\d+)M)?
            (?:(?P<seconds>\d+(?:\.\d+)?)S)?
        )?
        $
        """,
        re.VERBOSE,
    )

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

    def resource(self, name: str, kind: str | None = None) -> ODataResource:
        return ODataResource(self, name, kind)
    
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
        # TODO: validate for V2/V4 differences
        self._check_version()
        if type.is_string:
            return self.quoted_string(value)
        if type.is_binary:
            if isinstance(value, (bytes, bytearray)):
                return f"binary'{self.to_base64url(value)}'"
            raise ValueError(f"Expected bytes or bytearray for binary type, got {str(type)}")
        if type.is_enum:
            return f"{type.name}'{str(value)}'"
        tc = type.code
        if tc == EdmTypeCode.DateTime and isinstance(value, datetime):
            if value.tzinfo is not None:
                raise ValueError(f"value_in_path: DateTime value must not have zone offset (found {value})")
            return self.percent_encode(value.isoformat())  # colons must be percent-encoded in path segments
        if tc == EdmTypeCode.DateTimeOffset and isinstance(value, datetime):
            # Note: colons must be percent-encoded in path segments
            if value.tzinfo is None:  # some conversion layer (e.g. DB) might have dropped UTC offset
                return self.percent_encode(value.isoformat() + "Z")
            return self.percent_encode(value.isoformat())
        if tc == EdmTypeCode.Duration or tc == EdmTypeCode.Time:
            return self.value_in_body(value, type)
        return str(value)

    def value_in_body(self, value: Any, type: EdmType) -> Any:
        # TODO: validate for V2/V4 differences
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
        tc = type.code
        if tc == EdmTypeCode.DateTime and isinstance(value, datetime):
            if value.tzinfo is not None:
                raise ValueError(f"value_in_body: DateTime value must not have zone offset (found {value})")
            return self.percent_encode(value.isoformat())  # colons must be percent-encoded in path segments
        if tc == EdmTypeCode.DateTimeOffset and isinstance(value, datetime):
            # Note: colons must be percent-encoded in path segments
            if value.tzinfo is None:  # some conversion layer (e.g. DB) might have dropped UTC offset
                return value.isoformat() + "Z"
            return value.isoformat()
        if tc == EdmTypeCode.Duration or tc == EdmTypeCode.Time:
            if isinstance(value, Decimal):
                return f"PT{value}S"
            if isinstance(value, float):
                formatted = f"{value:.9f}".rstrip("0").rstrip(".")
                return f"PT{formatted}S"
            return value
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

    def verify_patch(self, patch_body: dict, get_response: dict, field_types: dict[str, EdmType]) -> list[str]:
        """
        Compare a PATCH request body against a GET response body.
        Returns a list of mismatch descriptions. An empty list means all patched properties
        match the retrieved values. ISO 8601 date/time strings are normalized before comparison
        (covers DateTimeOffset timezone variants such as Z vs +00:00).
        field_types maps dotted field paths (e.g. "address.city") to their EdmType.
        Fields not present in patch_body are skipped.
        """
        mismatches = []
        for path, edm_type in field_types.items():
            expected = self._get_by_path(patch_body, path)
            if expected is _MISSING:
                continue  # field not in this patch, skip
            received = self._get_by_path(get_response, path)
            if received is _MISSING:
                mismatches.append(f"{path}: not present in GET response")
                continue
            if not self._patch_values_equal(expected, received, edm_type):
                mismatches.append(f"{path}: expected {expected}, received {received}")
        return mismatches

    def _get_by_path(self, obj: dict, path: str) -> Any:
        for part in path.split("."):
            if not isinstance(obj, dict) or part not in obj:
                return _MISSING
            obj = obj[part]
        return obj

    def _patch_values_equal(self, a: Any, b: Any, type: EdmType) -> bool:
        if a == b:
            return True
        if a is None or b is None:
            return False
        tc = type.code
        if tc == EdmTypeCode.DateTime or tc == EdmTypeCode.DateTimeOffset:
            # Assuming that either both (or neither) of a and b have zone offset
            da = datetime.fromisoformat(str(a))
            db = datetime.fromisoformat(str(b))
            return da == db
        if tc == EdmTypeCode.TimeOfDay:
            ta = time.fromisoformat(str(a))
            tb = time.fromisoformat(str(b))
            return ta == tb
        if tc == EdmTypeCode.Duration or tc == EdmTypeCode.Time:
            # Time is used in OData V2, Duration in V4.
            # Both are represented as xs:duration strings.
            sa = self._xs_duration_seconds(str(a))
            sb = self._xs_duration_seconds(str(b))
            return sa == sb
        # TODO: Edm.Geo*
        return False

    def _xs_duration_seconds(self, duration: str) -> Decimal:
        """
        Parse an xs:dayTimeDuration value. Return total seconds.
        """
        match = self._DAY_TIME_DURATION_PATTERN.match(duration)
        if not match:
            raise ValueError(f"Invalid xs:duration (days/time only): {duration}")
        parts = {
            key: Decimal(value) if value else Decimal(0)
            for key, value in match.groupdict().items()
            if key != "sign"
        }
        sign = _DECIMAL_NEG_ONE if match.group("sign") else _DECIMAL_ONE
        total_seconds = (
            parts["days"] * _SECONDS_PER_DAY
            + parts["hours"] * _SECONDS_PER_HOUR
            + parts["minutes"] * _SECONDS_PER_MINUTE
            + parts["seconds"]
        )
        return sign * total_seconds

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
    def __init__(self, odata: OData, name: str, kind: str | None = None) -> None:
        self.odata = odata
        self.name = name
        self.kind = kind
    
    def with_key(self, entity_key: list[tuple[str, Any, EdmType]]) -> str:
        return self.odata.entity_with_key(self.name, entity_key)
