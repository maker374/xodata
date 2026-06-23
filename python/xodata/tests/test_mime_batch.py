# WORK IN PROGRESS - DO NOT USE AND DO NOT SUGGEST CHANGES TO THIS FILE

from requests import Request, Response

from mime_batch import BatchRequest, BatchResponse, ChangeSetRequest, format_batch_request, parse_batch_response


def test_format_batch_request_with_nested_changeset() -> None:
	get_request = Request(
		method="GET",
		url="/odata/Customers?$top=1",
		headers={"Accept": "application/json"},
	)

	changeset = ChangeSetRequest(boundary="changeset_abc")
	changeset.append(
		Request(
			method="POST",
			url="/odata/Customers",
			json={"Name": "Alice"},
		)
	)
	changeset.append(
		Request(
			method="PATCH",
			url="/odata/Customers(1)",
			json={"Name": "Alice Updated"},
		)
	)

	batch = BatchRequest(parts=[get_request, changeset], boundary="batch_abc")
	content_type, payload = format_batch_request(batch)
	text = payload.decode("utf-8")

	assert content_type == "multipart/mixed; boundary=batch_abc"
	assert "--batch_abc" in text
	assert "Content-Type: application/http" in text
	assert "GET /odata/Customers?$top=1 HTTP/1.1" in text
	assert "Content-Type: multipart/mixed; boundary=changeset_abc" in text
	assert "POST /odata/Customers HTTP/1.1" in text
	assert "PATCH /odata/Customers(1) HTTP/1.1" in text
	assert '{"Name":"Alice"}' in text
	assert '{"Name":"Alice Updated"}' in text
	assert "--changeset_abc--" in text
	assert "--batch_abc--" in text


def test_parse_batch_response_with_nested_changeset() -> None:
	content_type = "multipart/mixed; boundary=batch_123"
	payload = (
		"--batch_123\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 200 OK\r\n"
		"Content-Type: application/json\r\n"
		"\r\n"
		"{\"value\":[{\"Id\":1}]}\r\n"
		"--batch_123\r\n"
		"Content-Type: multipart/mixed; boundary=changeset_456\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"--changeset_456\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 201 Created\r\n"
		"Content-Type: application/json\r\n"
		"\r\n"
		"{\"Id\":2}\r\n"
		"--changeset_456\r\n"
		"Content-Type: application/http\r\n"
		"Content-Transfer-Encoding: binary\r\n"
		"\r\n"
		"HTTP/1.1 204 No Content\r\n"
		"\r\n"
		"\r\n"
		"--changeset_456--\r\n"
		"--batch_123--\r\n"
	).encode("utf-8")

	parsed = parse_batch_response(content_type, payload)

	assert isinstance(parsed, BatchResponse)
	assert parsed.boundary == "batch_123"
	assert len(parsed.parts) == 2

	first = parsed.parts[0]
	assert isinstance(first, Response)
	assert first.status_code == 200
	assert first.json() == {"value": [{"Id": 1}]}

	nested = parsed.parts[1]
	assert isinstance(nested, BatchResponse)
	assert nested.boundary == "changeset_456"
	assert len(nested.parts) == 2
	assert isinstance(nested.parts[0], Response)
	assert nested.parts[0].status_code == 201
	assert nested.parts[0].json() == {"Id": 2}
	assert isinstance(nested.parts[1], Response)
	assert nested.parts[1].status_code == 204
	assert nested.parts[1].content == b""
