"""Tests for REST annotations."""

import pytest
from flaxon_spring_boot.rest import (
    GetMapping,
    PostMapping,
    PutMapping,
    DeleteMapping,
    PatchMapping,
    RequestMapping,
    RequestBody,
    RequestParam,
    PathVariable,
    RequestHeader,
)


class TestRestAnnotations:
    """Test REST annotation classes."""

    def test_get_mapping(self):
        """Test GetMapping annotation."""
        mapping = GetMapping("/test")
        assert mapping.path == "/test"
        assert mapping.method == "GET"

    def test_post_mapping(self):
        """Test PostMapping annotation."""
        mapping = PostMapping("/test")
        assert mapping.path == "/test"
        assert mapping.method == "POST"

    def test_put_mapping(self):
        """Test PutMapping annotation."""
        mapping = PutMapping("/test")
        assert mapping.path == "/test"
        assert mapping.method == "PUT"

    def test_delete_mapping(self):
        """Test DeleteMapping annotation."""
        mapping = DeleteMapping("/test")
        assert mapping.path == "/test"
        assert mapping.method == "DELETE"

    def test_patch_mapping(self):
        """Test PatchMapping annotation."""
        mapping = PatchMapping("/test")
        assert mapping.path == "/test"
        assert mapping.method == "PATCH"

    def test_request_mapping(self):
        """Test RequestMapping annotation."""
        mapping = RequestMapping(
            path="/test",
            method="OPTIONS",
            consumes="application/json",
            produces="application/json",
        )
        assert mapping.path == "/test"
        assert mapping.method == "OPTIONS"
        assert mapping.consumes == "application/json"
        assert mapping.produces == "application/json"

    def test_request_body(self):
        """Test RequestBody annotation."""
        body = RequestBody(required=True)
        assert body.required is True

        body = RequestBody(required=False)
        assert body.required is False

    def test_request_param(self):
        """Test RequestParam annotation."""
        param = RequestParam(name="test", required=True, default="default")
        assert param.name == "test"
        assert param.required is True
        assert param.default == "default"

    def test_path_variable(self):
        """Test PathVariable annotation."""
        path_var = PathVariable(name="id", required=True)
        assert path_var.name == "id"
        assert path_var.required is True

    def test_request_header(self):
        """Test RequestHeader annotation."""
        header = RequestHeader(name="X-Test", required=True, default="default")
        assert header.name == "X-Test"
        assert header.required is True
        assert header.default == "default"