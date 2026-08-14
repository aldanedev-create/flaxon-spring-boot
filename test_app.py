"""Test app for flaxon-spring-boot."""

import asyncio
from flaxon import Flaxon
from flaxon_spring_boot import (
    SpringBootPlugin,
    Component,
    Service,
    Repository,
    Autowired,
    RestController,
    GetMapping,
    PostMapping,
    Transactional,
    Scheduled,
    Profile,
    Aspect,
    Before,
    After,
)

# ============================================================
# 1. Create Flaxon App
# ============================================================

app = Flaxon("spring-boot-test", debug=True)

# ============================================================
# 2. Load Spring Boot Plugin (Using correct async method)
# ============================================================

async def load_plugin():
    """Load Spring Boot plugin."""
    await app.plugins.load_plugin(SpringBootPlugin(
        profiles=["dev"],
        autoconfigure=True,
        actuator_enabled=True,
        scheduling_enabled=True,
        aop_enabled=True,
    ))

# ============================================================
# 3. Define Components
# ============================================================

@Component
class DatabaseConfig:
    """Database configuration component."""
    
    def __init__(self):
        self.url = "postgresql://localhost:5432/testdb"
        self.pool_size = 10


@Repository
class UserRepository:
    """User repository with in-memory storage."""
    
    def __init__(self):
        self._data = {}
        self._counter = 1
    
    async def find_all(self):
        return list(self._data.values())
    
    async def find_by_id(self, id: int):
        return self._data.get(id)
    
    async def save(self, data: dict):
        if "id" not in data:
            data["id"] = self._counter
            self._counter += 1
        self._data[data["id"]] = data
        return data
    
    async def delete(self, id: int):
        if id in self._data:
            del self._data[id]
            return True
        return False


@Service
class UserService:
    """User service with business logic."""
    
    @Autowired
    def __init__(self, repo: UserRepository, config: DatabaseConfig):
        self.repo = repo
        self.config = config
    
    async def get_all_users(self):
        return await self.repo.find_all()
    
    async def get_user(self, id: int):
        return await self.repo.find_by_id(id)
    
    @Transactional
    async def create_user(self, data: dict):
        if not data.get("name"):
            raise ValueError("Name is required")
        if not data.get("email"):
            raise ValueError("Email is required")
        
        user = await self.repo.save(data)
        return user
    
    async def delete_user(self, id: int):
        return await self.repo.delete(id)


# ============================================================
# 4. Define REST Controllers
# ============================================================

@RestController("/api/users")
class UserController:
    """User REST controller."""
    
    @Autowired
    def __init__(self, service: UserService):
        self.service = service
    
    @GetMapping
    async def get_users(self):
        """Get all users."""
        return await self.service.get_all_users()
    
    @GetMapping("/{id}")
    async def get_user(self, id: int):
        """Get user by ID."""
        user = await self.service.get_user(id)
        if not user:
            return {"error": "User not found"}, 404
        return user
    
    @PostMapping
    async def create_user(self, request):
        """Create a new user."""
        data = await request.json()
        try:
            user = await self.service.create_user(data)
            return user, 201
        except ValueError as e:
            return {"error": str(e)}, 400


# ============================================================
# 5. Define Scheduled Tasks
# ============================================================

@Component
class ReportScheduler:
    """Scheduled report generator."""
    
    @Scheduled(fixed_delay=10000)
    async def generate_report(self):
        import datetime
        print(f"[Scheduler] Report at {datetime.datetime.now()}")


# ============================================================
# 6. Define Profile-Specific Beans
# ============================================================

@Component
@Profile("dev")
class DevConfig:
    def __init__(self):
        self.env = "dev"
        self.debug = True


@Component
@Profile("prod")
class ProdConfig:
    def __init__(self):
        self.env = "prod"
        self.debug = False


# ============================================================
# 7. Define AOP Aspect
# ============================================================

@Aspect
class LoggingAspect:
    """Logging aspect for all service methods."""
    
    @Before("execution(* UserService.*(..))")
    async def log_before(self, join_point):
        print(f"[Aspect] Calling: {join_point.method.__name__}")
    
    @After("execution(* UserService.*(..))")
    async def log_after(self, join_point, result=None):
        print(f"[Aspect] Completed: {join_point.method.__name__}")


# ============================================================
# 8. Routes
# ============================================================

@app.get("/")
async def home():
    spring_boot = app.state.spring_boot if hasattr(app.state, "spring_boot") else None
    return {
        "message": "Welcome to Flaxon Spring-Boot Test App!",
        "endpoints": {
            "users": "/api/users",
            "user_by_id": "/api/users/{id}",
            "actuator": "/actuator/health",
            "profile": "/profile",
        },
        "profiles": spring_boot.get_active_profiles() if spring_boot else [],
        "status": "running",
    }


@app.get("/profile")
async def profile_info(request):
    spring_boot = request.app.state.spring_boot if hasattr(request.app.state, "spring_boot") else None
    if not spring_boot:
        return {"error": "Spring Boot not initialized"}, 503
    
    return {
        "active_profiles": spring_boot.get_active_profiles(),
        "initialized": spring_boot.is_initialized(),
        "bean_count": len(spring_boot.application_context.get_bean_names()),
        "beans": spring_boot.application_context.get_bean_names()[:10],
    }


# ============================================================
# 9. Seed Data Function
# ============================================================

async def seed_data():
    """Seed initial data."""
    # Wait for plugin to initialize
    await asyncio.sleep(0.5)
    
    spring_boot = app.state.spring_boot
    if not spring_boot:
        print("[Startup] Spring Boot not initialized yet")
        return
    
    service = spring_boot.get_bean("userservice", UserService)
    
    sample_users = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]
    
    for user_data in sample_users:
        try:
            await service.create_user(user_data)
        except Exception:
            pass
    
    print(f"[Startup] Seeded {len(sample_users)} users")

# ============================================================
# 10. Run the App
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    # Load plugin before starting
    asyncio.run(load_plugin())
    
    # Seed data
    asyncio.run(seed_data())
    
    print("🚀 Starting Flaxon Spring-Boot Test App...")
    print("📍 http://localhost:8000")
    print("📍 http://localhost:8000/api/users")
    print("📍 http://localhost:8000/actuator/health")
    print("📍 http://localhost:8000/profile")
    print()
    print("Press Ctrl+C to stop")
    
    uvicorn.run("test_app:app", host="127.0.0.1", port=8000, reload=True)