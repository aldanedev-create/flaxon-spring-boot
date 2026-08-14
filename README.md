# Flaxon Spring-Boot

<p align="center">
  <img src="https://raw.githubusercontent.com/aldanedev-create/Flaxon-Backend-Framework/main/assets/flaxon.png" alt="Flaxon Logo" width="200"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/flaxon/"><img src="https://img.shields.io/pypi/v/flaxon.svg" alt="PyPI version"></a>
  <a href="https://github.com/aldanedev-create/Flaxon-Backend-Framework/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"></a>
</p>

**Spring Boot-style patterns for Flaxon** — Dependency Injection, AOP, REST Controllers, and more.

## Table of Contents

* [What is this?](#what-is-this)
* [Why Spring Boot Patterns in Python?](#why-spring-boot-patterns-in-python)
* [Installation](#installation)
* [Quick Start](#quick-start)

  * [1. Load the Plugin](#1-load-the-plugin)
  * [2. Create a Service](#2-create-a-service)
  * [3. Create a REST Controller](#3-create-a-rest-controller)
  * [4. Run the App](#4-run-the-app)
* [Features](#features)

  * [Dependency Injection](#dependency-injection)
  * [AOP (Aspect-Oriented Programming)](#aop-aspect-oriented-programming)
  * [Scheduled Tasks](#scheduled-tasks)
  * [Transactional](#transactional)
  * [Application Properties](#application-properties)
  * [Actuator Endpoints](#actuator-endpoints)
  * [Profiles](#profiles)
* [File Structure](#file-structure)
* [Spring vs Flaxon Spring-Boot](#spring-vs-flaxon-spring-boot)
* [Requirements](#requirements)
* [License](#license)
* [Support](#support)

## What is this?

Flaxon Spring-Boot brings the battle-tested patterns of **Spring Boot** to Python. It provides:

* 🔄 **Dependency Injection** — `@Autowired`, `@Component`, `@Service`, `@Repository`
* 🎯 **AOP (Aspect-Oriented)** — `@Aspect`, `@Before`, `@After`, `@Around`
* 🚀 **Auto-Configuration** — Auto-detect and configure components
* 📝 **Application Properties** — `application.yml` / `application.properties` support
* 🎭 **Profiles** — `@Profile("dev")`, `@Profile("prod")` environment-specific beans
* ⏰ **Scheduled Tasks** — `@Scheduled(cron="* * * * *")`
* 💾 **Transactional** — `@Transactional` for database operations
* 🌐 **REST Controllers** — `@RestController`, `@GetMapping`, `@PostMapping`
* 📊 **Spring Data JPA-style** — Repository interfaces with auto-CRUD
* 📈 **Actuator** — Health checks, metrics, info endpoints
* 📡 **Event Listeners** — `@EventListener` for application events
* ⚙️ **Configuration Properties** — `@ConfigurationProperties` for typed config

## Why Spring Boot Patterns in Python?

| Problem                          | Solution                                |
| -------------------------------- | --------------------------------------- |
| Manual dependency wiring         | `@Autowired` auto-wiring                |
| Boilerplate CRUD code            | `@Repository` + auto-CRUD               |
| Transaction boilerplate          | `@Transactional`                        |
| Manual scheduling setup          | `@Scheduled` cron/fixed-delay           |
| Cross-cutting concerns scattered | `@Aspect` AOP                           |
| Hard-coded configuration         | `application.yml` profiles              |
| No built-in health checks        | `/actuator/health`, `/actuator/metrics` |

## Installation

```bash
pip install flaxon-spring-boot
```

With dev dependencies:

```bash
pip install flaxon-spring-boot[dev]
```

## Quick Start

### 1. Load the Plugin

```python
from flaxon import Flaxon
from flaxon_spring_boot import SpringBootPlugin

app = Flaxon("my-app")

# Load Spring Boot plugin
app.plugins.load_plugin(SpringBootPlugin(
    profiles=["dev"],
    autoconfigure=True,
    actuator_enabled=True,
))
```

### 2. Create a Service

```python
from flaxon_spring_boot import Service, Autowired, Repository

@Service
class UserService:
    @Autowired
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_user(self, id: int):
        return await self.repo.find_by_id(id)

@Repository
class UserRepository:
    _data = {}

    async def find_by_id(self, id: int):
        return self._data.get(id)

    async def save(self, data: dict):
        self._data[data["id"]] = data
        return data
```

### 3. Create a REST Controller

```python
from flaxon_spring_boot import RestController, GetMapping, PostMapping, RequestBody

@RestController("/api/users")
class UserController:
    @Autowired
    def __init__(self, service: UserService):
        self.service = service

    @GetMapping("/{id}")
    async def get_user(self, id: int):
        return await self.service.get_user(id)

    @PostMapping
    async def create_user(self, @RequestBody data: dict):
        return await self.service.create_user(data)
```

### 4. Run the App

```bash
flaxon run app:app --reload
```

## Features

### Dependency Injection

```python
from flaxon_spring_boot import Component, Autowired, Service

@Component
class DatabaseConfig:
    def __init__(self):
        self.url = "postgresql://localhost:5432/mydb"

@Service
class UserService:
    @Autowired
    def __init__(self, config: DatabaseConfig, repo: UserRepository):
        self.config = config
        self.repo = repo
```

### AOP (Aspect-Oriented Programming)

```python
from flaxon_spring_boot import Aspect, Before, After, Pointcut

@Aspect
class LoggingAspect:
    @Pointcut("execution(* UserService.*(..))")
    def service_methods(self):
        pass

    @Before("service_methods")
    def log_before(self, join_point):
        print(f"Calling: {join_point.method}")

    @After("service_methods")
    def log_after(self, join_point, result):
        print(f"Returned: {result}")
```

### Scheduled Tasks

```python
from flaxon_spring_boot import Scheduled, Component

@Component
class ReportScheduler:
    @Scheduled(cron="0 0 * * * *")  # Every hour
    async def generate_report(self):
        await report_service.generate()

    @Scheduled(fixed_delay=5000)  # Every 5 seconds
    async def ping_health(self):
        print("Health check")
```

### Transactional

```python
from flaxon_spring_boot import Transactional, Service

@Service
class OrderService:
    @Transactional
    async def create_order(self, order_data):
        # Auto-rollback on exception
        order = await order_repo.save(order_data)
        await inventory_repo.update(order.items)
        return order
```

### Application Properties

```yaml
# application.yml
spring:
  datasource:
    url: postgresql://localhost:5432/mydb
    username: admin
    password: secret

app:
  name: My Flaxon App
  version: 1.0.0

logging:
  level: DEBUG
```

```python
from flaxon_spring_boot import ConfigurationProperties

@ConfigurationProperties("app")
class AppConfig:
    name: str
    version: str
```

### Actuator Endpoints

| Endpoint            | Purpose                   |
| ------------------- | ------------------------- |
| `/actuator/health`  | Application health status |
| `/actuator/info`    | Application information   |
| `/actuator/metrics` | Performance metrics       |
| `/actuator/routes`  | Registered routes         |
| `/actuator/beans`   | Managed beans             |

### Profiles

```python
from flaxon_spring_boot import Profile, Component

@Component
@Profile("dev")
class DevDatabaseConfig:
    url = "postgresql://localhost:5432/dev"

@Component
@Profile("prod")
class ProdDatabaseConfig:
    url = "postgresql://production:5432/prod"
```

## File Structure

```text
```

## Spring vs Flaxon Spring-Boot

| Spring (Java)              | Flaxon Spring-Boot (Python) |
| -------------------------- | --------------------------- |
| `@Autowired`               | `@Autowired`                |
| `@Service`                 | `@Service`                  |
| `@Repository`              | `@Repository`               |
| `@RestController`          | `@RestController`           |
| `@GetMapping`              | `@GetMapping`               |
| `@Transactional`           | `@Transactional`            |
| `@Scheduled`               | `@Scheduled`                |
| `@Aspect`                  | `@Aspect`                   |
| `application.properties`   | `application.yml`           |
| `@Profile`                 | `@Profile`                  |
| Spring Boot Actuator       | Flaxon Actuator             |
| `@EventListener`           | `@EventListener`            |
| `@ConfigurationProperties` | `@ConfigurationProperties`  |

## Requirements

Python 3.11+

Flaxon 0.1.9+

## License

MIT License - See LICENSE file for details.

## Support

📚 Documentation

🐛 Issue Tracker

💬 Discussions
