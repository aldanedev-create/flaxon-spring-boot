"""Tests for annotations."""

import pytest
from flaxon_spring_boot.annotations import (
    Component,
    Service,
    Repository,
    Controller,
    RestController,
    Autowired,
    Value,
    ComponentScan,
    Configuration,
    Bean,
    Primary,
    Qualifier,
    Lazy,
    Scope,
)


class TestAnnotations:
    """Test annotation classes."""

    def test_component(self):
        """Test Component annotation."""
        @Component("test_component")
        class TestClass:
            pass

        assert hasattr(TestClass, '_spring_component')
        assert TestClass._spring_component is True
        assert TestClass._spring_component_name == "test_component"

    def test_component_default_name(self):
        """Test Component annotation with default name."""
        @Component
        class TestClass:
            pass

        assert TestClass._spring_component_name == "testclass"

    def test_service(self):
        """Test Service annotation."""
        @Service
        class TestService:
            pass

        assert hasattr(TestService, '_spring_component')
        assert hasattr(TestService, '_spring_service')
        assert TestService._spring_service is True

    def test_repository(self):
        """Test Repository annotation."""
        @Repository
        class TestRepository:
            pass

        assert hasattr(TestRepository, '_spring_component')
        assert hasattr(TestRepository, '_spring_repository')
        assert TestRepository._spring_repository is True

    def test_controller(self):
        """Test Controller annotation."""
        @Controller(path="/test")
        class TestController:
            pass

        assert hasattr(TestController, '_spring_controller')
        assert TestController._spring_controller_path == "/test"

    def test_rest_controller(self):
        """Test RestController annotation."""
        @RestController
        class TestRestController:
            pass

        assert hasattr(TestRestController, '_spring_controller')
        assert hasattr(TestRestController, '_spring_rest_controller')
        assert TestRestController._spring_rest_controller is True

    def test_autowired(self):
        """Test Autowired annotation."""
        @Autowired
        class TestClass:
            pass

        assert hasattr(TestClass, '_spring_autowired')
        assert TestClass._spring_autowired is True
        assert TestClass._spring_autowired_required is True

    def test_autowired_with_name(self):
        """Test Autowired annotation with name."""
        @Autowired(name="test_bean")
        class TestClass:
            pass

        assert TestClass._spring_autowired_name == "test_bean"

    def test_value(self):
        """Test Value annotation."""
        @Value(key="test.key", default="default")
        class TestClass:
            pass

        assert TestClass._spring_value is True
        assert TestClass._spring_value_key == "test.key"
        assert TestClass._spring_value_default == "default"

    def test_component_scan(self):
        """Test ComponentScan annotation."""
        @ComponentScan(packages=["test.package"])
        class TestClass:
            pass

        assert TestClass._spring_component_scan is True
        assert TestClass._spring_component_scan_packages == ["test.package"]

    def test_configuration(self):
        """Test Configuration annotation."""
        @Configuration
        class TestConfig:
            pass

        assert hasattr(TestConfig, '_spring_configuration')
        assert TestConfig._spring_configuration is True

    def test_bean(self):
        """Test Bean annotation."""
        def test_factory():
            pass

        @Bean(name="test_bean")
        def test_factory_with_bean():
            pass

        assert hasattr(test_factory_with_bean, '_spring_bean')
        assert test_factory_with_bean._spring_bean_name == "test_bean"

    def test_primary(self):
        """Test Primary annotation."""
        @Primary
        class TestClass:
            pass

        assert TestClass._spring_primary is True

    def test_qualifier(self):
        """Test Qualifier annotation."""
        @Qualifier("test_bean")
        class TestClass:
            pass

        assert TestClass._spring_qualifier == "test_bean"

    def test_lazy(self):
        """Test Lazy annotation."""
        @Lazy
        class TestClass:
            pass

        assert TestClass._spring_lazy is True

    def test_scope(self):
        """Test Scope annotation."""
        @Scope("prototype")
        class TestClass:
            pass

        assert TestClass._spring_scope == "prototype"