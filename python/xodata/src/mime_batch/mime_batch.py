# WORK IN PROGRESS - DO NOT USE AND DO NOT SUGGEST CHANGES TO THIS FILE

# Copyright (c) 2026 maker374
# https://github.com/maker374/xodata

from __future__ import annotations

import json
from dataclasses import dataclass, field
from email import policy
from email.message import Message
from email.parser import BytesParser
from typing import Mapping, Sequence
from uuid import uuid4

from requests import Request, Response
from requests.structures import CaseInsensitiveDict


PartRequest = Request | "BatchRequest"
PartResponse = Response | "BatchResponse"


def _parse_content_type(value: str) -> tuple[str, dict[str, str]]:
	message = Message()
	message["content-type"] = value
	content_type = message.get_content_type()
	params: dict[str, str] = {}
	for key, param_value in message.get_params(header="content-type"):
		if key.lower() != "content-type":
			params[key.lower()] = str(param_value)
	return content_type.lower(), params


def _new_boundary(prefix: str) -> str:
	return f"{prefix}_{uuid4().hex}"


def _normalize_newlines(value: str) -> str:
	return value.replace("\r\n", "\n").replace("\r", "\n")


def _ensure_bytes(value: bytes | bytearray | str | None) -> bytes:
	if value is None:
		return b""
	if isinstance(value, (bytes, bytearray)):
		return bytes(value)
	return str(value).encode("utf-8")


@dataclass(slots=True)
class BatchRequest:
	"""Represents an OData batch request or nested changeset."""

	parts: list[PartRequest] = field(default_factory=list)
	boundary: str = ""

	def __post_init__(self) -> None:
		if not self.boundary:
			self.boundary = _new_boundary("batch")

	def append(self, part: PartRequest) -> None:
		self.parts.append(part)

	def to_multipart_mixed(self) -> tuple[str, bytes]:
		return format_batch_request(self)


class ChangeSetRequest(BatchRequest):
	"""Semantic alias for nested write operations in OData batch."""

	def __post_init__(self) -> None:
		if not self.boundary:
			self.boundary = _new_boundary("changeset")


@dataclass(slots=True)
class BatchResponse:
	"""Represents an OData batch response or nested changeset response."""

	parts: list[PartResponse] = field(default_factory=list)
	boundary: str = ""

	def append(self, part: PartResponse) -> None:
		self.parts.append(part)


class ChangeSetResponse(BatchResponse):
	"""Semantic alias for nested OData changeset responses."""


def _format_request_headers(headers: Mapping[str, str] | None) -> list[str]:
	if not headers:
		return []
	return [f"{key}: {value}" for key, value in headers.items()]


def _request_body_bytes(request: Request) -> bytes:
	if request.json is not None:
		payload = json.dumps(request.json, separators=(",", ":"))
		return payload.encode("utf-8")
	return _ensure_bytes(request.data)


def _format_application_http_request(request: Request) -> bytes:
	method = (request.method or "GET").upper()
	url = request.url or ""
	lines = [f"{method} {url} HTTP/1.1"]
	lines.extend(_format_request_headers(request.headers))
	body = _request_body_bytes(request)
	if request.json is not None and not any(k.lower() == "content-type" for k in (request.headers or {})):
		lines.append("Content-Type: application/json")
	payload = "\r\n".join(lines).encode("utf-8") + b"\r\n\r\n"
	if body:
		payload += body
	return payload


def _format_multipart_part_request(part: PartRequest) -> bytes:
	if isinstance(part, BatchRequest):
		nested_content_type, nested_payload = format_batch_request(part)
		header = (
			"Content-Type: "
			+ nested_content_type
			+ "\r\n"
			+ "Content-Transfer-Encoding: binary\r\n\r\n"
		)
		return header.encode("utf-8") + nested_payload
	if isinstance(part, Request):
		header = "Content-Type: application/http\r\nContent-Transfer-Encoding: binary\r\n\r\n"
		return header.encode("utf-8") + _format_application_http_request(part)
	raise TypeError(f"Unsupported batch request part type: {type(part)!r}")


def format_batch_request(batch: BatchRequest) -> tuple[str, bytes]:
	"""Format a batch request as multipart/mixed payload.

	Returns content type header value and encoded payload bytes.
	"""

	boundary = batch.boundary
	chunks: list[bytes] = []
	for part in batch.parts:
		chunks.append(f"--{boundary}\r\n".encode("utf-8"))
		chunks.append(_format_multipart_part_request(part))
		chunks.append(b"\r\n")
	chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
	return f"multipart/mixed; boundary={boundary}", b"".join(chunks)


def _split_http_message(payload: bytes) -> tuple[list[str], bytes]:
	text = payload.decode("latin1")
	normalized = _normalize_newlines(text)
	marker = "\n\n"
	index = normalized.find(marker)
	if index < 0:
		return normalized.split("\n"), b""
	header_block = normalized[:index]
	body_text = normalized[index + len(marker) :]
	return header_block.split("\n"), body_text.encode("latin1")


def _parse_headers(lines: Sequence[str]) -> CaseInsensitiveDict:
	headers: CaseInsensitiveDict = CaseInsensitiveDict()
	for line in lines:
		line = line.strip()
		if not line:
			continue
		if ":" not in line:
			continue
		key, value = line.split(":", 1)
		headers[key.strip()] = value.strip()
	return headers


def _parse_application_http_response(payload: bytes) -> Response:
	lines, body = _split_http_message(payload)
	if not lines or not lines[0].startswith("HTTP/"):
		raise ValueError("Invalid application/http payload: missing HTTP status line")

	status_line = lines[0].strip().split(" ", 2)
	if len(status_line) < 2:
		raise ValueError("Invalid HTTP status line in batch response")

	response = Response()
	response.status_code = int(status_line[1])
	response.reason = status_line[2] if len(status_line) > 2 else ""
	response.headers = _parse_headers(lines[1:])
	response._content = body
	response.encoding = response.encoding or "utf-8"
	return response


def _parse_message_part(part_message) -> PartResponse:
	content_type = part_message.get_content_type().lower()
	if content_type == "application/http":
		payload = part_message.get_payload(decode=True)
		if payload is None:
			payload = b""
		return _parse_application_http_response(payload)
	if content_type == "multipart/mixed":
		boundary = part_message.get_param("boundary")
		nested = BatchResponse(boundary=boundary or "")
		for nested_part in part_message.iter_parts():
			nested.append(_parse_message_part(nested_part))
		return nested
	raise ValueError(f"Unsupported batch response part content type: {content_type}")


def parse_batch_response(content_type: str, body: bytes | bytearray | str) -> BatchResponse:
	"""Parse a multipart/mixed OData batch response into Response objects."""

	parsed_type, params = _parse_content_type(content_type)
	if parsed_type != "multipart/mixed":
		raise ValueError(f"Expected multipart/mixed response, got {parsed_type}")
	boundary = params.get("boundary")
	if not boundary:
		raise ValueError("multipart/mixed response missing boundary parameter")

	payload = _ensure_bytes(body)
	envelope = (
		f"Content-Type: multipart/mixed; boundary={boundary}\r\nMIME-Version: 1.0\r\n\r\n".encode(
			"utf-8"
		)
		+ payload
	)
	message = BytesParser(policy=policy.default).parsebytes(envelope)

	parsed = BatchResponse(boundary=boundary)
	for part in message.iter_parts():
		parsed.append(_parse_message_part(part))
	return parsed


__all__ = [
	"BatchRequest",
	"BatchResponse",
	"ChangeSetRequest",
	"ChangeSetResponse",
	"format_batch_request",
	"parse_batch_response",
]
