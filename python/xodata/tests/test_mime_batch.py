from requests import Request, Response
from mime_batch import BatchRequest, BatchResponse, format_batch_request, parse_batch_response, post_batch_request


class _StubSession:
	def __init__(self, request_response: Response | None = None, post_response: Response | None = None) -> None:
		self._request_response = request_response
		self._post_response = post_response

	def request(self, **kwargs):
		return self._request_response

	def post(self, *args, **kwargs):
		return self._post_response


def test_batch_request_is_full() -> None:
	request = Request(method="GET", url="/odata/Customers")

	unlimited = BatchRequest()
	assert unlimited.is_full is False

	batch = BatchRequest(part_limit=2)
	assert batch.is_full is False
	batch.append(request)
	assert batch.is_full is False
	batch.append(request)
	assert batch.is_full is True


def test_post_batch_request_propagates_part_limit_single_unbatched() -> None:
	batch_request = BatchRequest(part_limit=5)
	batch_request.append(Request(method="GET", url="/odata/Customers(1)"))

	response = Response()
	response.status_code = 200
	response._content = b"{}"

	session = _StubSession(request_response=response)
	parsed = post_batch_request(
		service_root_url="https://example.test",
		session=session,
		request=batch_request,
		send_single_as_unbatched=True,
	)

	assert parsed.part_limit == batch_request.part_limit
	assert len(parsed.parts) == 1


def test_post_batch_request_propagates_part_limit_batch() -> None:
	batch_request = BatchRequest(part_limit=5)
	batch_request.append(Request(method="GET", url="/odata/Customers(1)"))

	response = Response()
	response.status_code = 200
	response.headers["Content-Type"] = "multipart/mixed; boundary=B_123"
	response._content = (
		"--B_123\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 200 OK\r\n"
		"Content-Type: application/json\r\n"
		"\r\n"
		"{}\r\n"
		"--B_123--\r\n"
	).encode("utf-8")

	session = _StubSession(post_response=response)
	parsed = post_batch_request(
		service_root_url="https://example.test",
		session=session,
		request=batch_request,
	)

	assert parsed.part_limit == batch_request.part_limit
	assert len(parsed.parts) == 1

def test_format_batch_request_with_nested_change_set() -> None:
	get_request = Request(
		method="GET",
		url="/odata/Customers?$top=1",
		headers={"Accept": "application/json"},
	)

	change_set = BatchRequest(boundary="C_456")
	change_set.append(
		Request(
			method="POST",
			url="/odata/Customers",
			json={"Name": "Alice"},
		)
	)
	change_set.append(
		Request(
			method="PATCH",
			url="/odata/Customers(1)",
			json={"Name": "Alice Updated"},
		)
	)

	batch = BatchRequest(parts=[get_request, change_set], boundary="B_123")
	payload = format_batch_request(batch)
	text = payload.decode("utf-8")

	assert batch.content_type == "multipart/mixed; boundary=B_123"
	assert "--B_123" in text
	assert "Content-Type: application/http" in text
	assert "GET /odata/Customers?$top=1 HTTP/1.1" in text
	assert "Content-Type: multipart/mixed; boundary=C_456" in text
	assert "POST /odata/Customers HTTP/1.1" in text
	assert "PATCH /odata/Customers(1) HTTP/1.1" in text
	assert '{"Name":"Alice"}' in text
	assert '{"Name":"Alice Updated"}' in text
	assert "--C_456--" in text
	assert "--B_123--" in text

def test_parse_batch_response_with_nested_change_set() -> None:
	content_type = "multipart/mixed; boundary=B_123"
	payload = (
		"--B_123\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 200 OK\r\n"
		"Content-Type: application/json\r\n"
		"\r\n"
		"{\"value\":[{\"Id\":1}]}\r\n"
		"--B_123\r\n"
		"Content-Type: multipart/mixed; boundary=C_456\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"--C_456\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 201 Created\r\n"
		"Content-Type: application/json\r\n"
		"\r\n"
		"{\"Id\":2}\r\n"
		"--C_456\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 204 No Content\r\n"
		"\r\n"
		"\r\n"
		"--C_456--\r\n"
		"--B_123--\r\n"
	).encode("utf-8")

	parsed = parse_batch_response(content_type, payload)

	assert isinstance(parsed, BatchResponse)
	assert parsed.boundary == "B_123"
	assert len(parsed.parts) == 2

	first = parsed.parts[0]
	assert isinstance(first, Response)
	assert first.status_code == 200
	assert first.json() == {"value": [{"Id": 1}]}

	nested = parsed.parts[1]
	assert isinstance(nested, BatchResponse)
	assert nested.boundary == "C_456"
	assert len(nested.parts) == 2
	assert isinstance(nested.parts[0], Response)
	assert nested.parts[0].status_code == 201
	assert nested.parts[0].json() == {"Id": 2}
	assert isinstance(nested.parts[1], Response)
	assert nested.parts[1].status_code == 204
	assert nested.parts[1].content == b""
