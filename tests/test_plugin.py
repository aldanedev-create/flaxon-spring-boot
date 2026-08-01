"""Tests for SpringBootPlugin."""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch

from flaxon import Flaxon
from flaxon_spring_boot import SpringBootPlugin
from flaxon_spring_boot.plugin import SpringBootConfig


class TestSpringBootPlugin:
    """Test SpringBootPlugin class."""

    def test_plugin_initialization(self):
        """Test basic plugin initialization."""
        plugin = SpringBootPlugin(
            profiles=["dev"],
            autoconfigure=True,
            actuator_enabled=True,
        )

        assert plugin.config.profiles == ["dev"]
        assert plugin.config.autoconfigure is True
        assert plugin.config.actuator_enabled is True
        assert plugin.config.scheduling_enabled is True
        assert plugin.config.aop_enabled is True
        assert plugin.name == "spring-boot"
        assert plugin.version == "0.1.0"

    def test_plugin_from_env(self, monkeypatch):
        """Test plugin loads from environment variables."""
        monkeypatch.setenv("SPRING_PROFILES_ACTIVE", "prod,staging")
        monkeypatch.setenv("SPRING_AUTOCONFIGURE", "false")
        monkeypatch.setenv("SPRING_ACTUATOR_ENABLED", "false")
        monkeypatch.setenv("SPRING_SCHEDULING_ENABLED", "false")
        monkeypatch.setenv("SPRING_AOP_ENABLED", "false")

        plugin = SpringBootPlugin()

        assert plugin.config.profiles == ["prod", "staging"]
        assert plugin.config.autoconfigure is False
        assert plugin.config.actuator_enabled is False
        assert plugin.config.scheduling_enabled is False
        assert plugin.config.aop_enabled is False

    def test_plugin_from_config(self):
        """Test plugin from Flaxon config."""
        config = {
            "SPRING_PROFILES_ACTIVE": "test",
            "SPRING_AUTOCONFIGURE": False,
            "SPRING_ACTUATOR_ENABLED": False,
            "SPRING_SCHEDULING_ENABLED": False,
            "SPRING_AOP_ENABLED": False,
            "SPRING_REPOSITORY_ENABLED": False,
        }

        plugin = SpringBootPlugin.from_config(config)

        assert plugin.config.profiles == ["test"]
        assert plugin.config.autoconfigure is False
        assert plugin.config.actuator_enabled is False
        assert plugin.config.scheduling_enabled is False
        assert plugin.config.aop_enabled is False

    def test_plugin_defaults(self):
        """Test plugin default values."""
        plugin = SpringBootPlugin()

        assert plugin.config.profiles == ["default"]
        assert plugin.config.autoconfigure is True
        assert plugin.config.actuator_enabled is True
        assert plugin.config.scheduling_enabled is True
        assert plugin.config.aop_enabled is True
        assert plugin.config.repository_enabled is True

    def test_plugin_has_name_and_version(self):
        """Test plugin has name and version attributes."""
        plugin = SpringBootPlugin()

        assert plugin.name == "spring-boot"
        assert plugin.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_plugin_setup(self):
        """Test plugin setup."""
        app = Flaxon("test-app")
        plugin = SpringBootPlugin()

        plugin.setup(app)

        assert hasattr(app.state, "spring_boot")
        assert app.state.spring_boot is plugin
        assert plugin._app is app
        assert plugin._initialized is True

    def test_plugin_get_bean(self):
        """Test get_bean method."""
        app = Flaxon("test-app")
        plugin = SpringBootPlugin()
        plugin.setup(app)

        # Register a bean
        class TestService:
            pass

        plugin.application_context.register_singleton("test_service", TestService())

        bean = plugin.get_bean("test_service")
        assert isinstance(bean, TestService)

    def test_plugin_get_beans(self):
        """Test get_beans method."""
        app = Flaxon("test-app")
        plugin = SpringBootPlugin()
        plugin.setup(app)

        class TestService:
            pass

        plugin.application_context.register_singleton("test1", TestService())
        plugin.application_context.register_singleton("test2", TestService())

        beans = plugin.get_beans(TestService)
        assert len(beans) == 2

    def test_plugin_get_active_profiles(self):
        """Test get_active_profiles method."""
        plugin = SpringBootPlugin(profiles=["dev", "test"])
        assert plugin.get_active_profiles() == ["dev", "test"]

    def test_plugin_get_property(self):
        """Test get_property method."""
        plugin = SpringBootPlugin()
        plugin.properties_loader._properties["test.key"] = "test_value"

        value = plugin.get_property("test.key")
        assert value == "test_value"

        default = plugin.get_property("missing.key", "default")
        assert default == "default"

    def test_plugin_get_required_property(self):
        """Test get_required_property method."""
        plugin = SpringBootPlugin()
        plugin.properties_loader._properties["test.key"] = "test_value"

        value = plugin.get_required_property("test.key")
        assert value == "test_value"

        with pytest.raises(ValueError):
            plugin.get_required_property("missing.key")

    def test_plugin_is_initialized(self):
        """Test is_initialized method."""
        plugin = SpringBootPlugin()
        assert plugin.is_initialized() is False

        app = Flaxon("test-app")
        plugin.setup(app)
        assert plugin.is_initialized() is True