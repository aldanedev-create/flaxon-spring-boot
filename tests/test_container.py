"""Tests for ApplicationContext."""

import pytest
from unittest.mock import Mock

from flaxon_spring_boot.container import (
    ApplicationContext,
    BeanDefinition,
    BeanScope,
)


class TestApplicationContext:
    """Test ApplicationContext class."""

    def test_context_initialization(self):
        """Test context initialization."""
        context = ApplicationContext()
        assert context._beans == {}
        assert context._bean_definitions == {}
        assert context._bean_types == {}
        assert context.is_initialized() is False

    def test_register_bean_definition(self):
        """Test registering a bean definition."""
        context = ApplicationContext()

        class TestService:
            pass

        definition = BeanDefinition(
            name="test_service",
            bean_type=TestService,
            scope=BeanScope.SINGLETON,
        )

        context.register_bean_definition(definition)

        assert context.has_bean("test_service")
        assert context.has_bean_type(TestService)

    def test_register_bean(self):
        """Test registering a bean instance."""
        context = ApplicationContext()

        class TestService:
            pass

        bean = TestService()
        context.register_bean("test_service", bean, TestService)

        assert context.has_bean("test_service")
        assert context.get_bean("test_service") is bean

    def test_get_bean_by_name(self):
        """Test getting a bean by name."""
        context = ApplicationContext()

        class TestService:
            pass

        bean = TestService()
        context.register_bean("test_service", bean, TestService)

        result = context.get_bean("test_service")
        assert result is bean

    def test_get_bean_by_type(self):
        """Test getting a bean by type."""
        context = ApplicationContext()

        class TestService:
            pass

        bean = TestService()
        context.register_bean("test_service", bean, TestService)

        result = context.get_bean_by_type(TestService)
        assert result is bean

    def test_get_bean_not_found(self):
        """Test getting a non-existent bean."""
        context = ApplicationContext()

        with pytest.raises(ValueError):
            context.get_bean("missing")

    def test_get_beans_by_type(self):
        """Test getting all beans of a type."""
        context = ApplicationContext()

        class TestService:
            pass

        bean1 = TestService()
        bean2 = TestService()
        context.register_bean("test1", bean1, TestService)
        context.register_bean("test2", bean2, TestService)

        beans = context.get_beans(TestService)
        assert len(beans) == 2
        assert bean1 in beans
        assert bean2 in beans

    def test_has_bean(self):
        """Test has_bean method."""
        context = ApplicationContext()

        class TestService:
            pass

        assert context.has_bean("test") is False

        bean = TestService()
        context.register_bean("test", bean, TestService)

        assert context.has_bean("test") is True

    def test_has_bean_type(self):
        """Test has_bean_type method."""
        context = ApplicationContext()

        class TestService:
            pass

        assert context.has_bean_type(TestService) is False

        bean = TestService()
        context.register_bean("test", bean, TestService)

        assert context.has_bean_type(TestService) is True

    def test_get_bean_names(self):
        """Test get_bean_names method."""
        context = ApplicationContext()

        class TestService:
            pass

        context.register_bean("test1", TestService(), TestService)
        context.register_bean("test2", TestService(), TestService)

        names = context.get_bean_names()
        assert "test1" in names
        assert "test2" in names

    def test_get_bean_types(self):
        """Test get_bean_types method."""
        context = ApplicationContext()

        class TestService:
            pass

        context.register_bean("test", TestService(), TestService)

        types = context.get_bean_types()
        assert TestService in types
        assert types[TestService] == ["test"]

    def test_register_singleton(self):
        """Test register_singleton method."""
        context = ApplicationContext()

        class TestService:
            pass

        bean = TestService()
        context.register_singleton("test", bean)

        assert context.get_singleton("test") is bean
        assert context.get_bean("test") is bean

    def test_clear(self):
        """Test clear method."""
        context = ApplicationContext()

        class TestService:
            pass

        context.register_singleton("test", TestService())
        context.clear()

        assert context.get_bean_names() == []
        assert context.is_initialized() is False