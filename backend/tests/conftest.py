import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, get_db
from app.main import app
from app.security import hash_password, create_access_token
from app.models import User

# Dedicated SQLite database for automated tests (isolated from dev database)
TEST_DATABASE_URL = "sqlite:///./test_expense_tracker.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all database tables before test session and drop them afterward."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean database session per test with automatic rollback/cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_a(db_session: Session) -> User:
    """Create User A for testing."""
    user = User(
        full_name="Alice Cybersecurity",
        email="alice@example.com",
        password_hash=hash_password("Password123!"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_b(db_session: Session) -> User:
    """Create User B for cross-user authorization testing."""
    user = User(
        full_name="Bob Security",
        email="bob@example.com",
        password_hash=hash_password("BobSecure123!"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_a_token(test_user_a: User) -> str:
    return create_access_token(data={"sub": str(test_user_a.id)})


@pytest.fixture
def user_b_token(test_user_b: User) -> str:
    return create_access_token(data={"sub": str(test_user_b.id)})


@pytest.fixture
def auth_client_a(db_session: Session, user_a_token: str) -> Generator[TestClient, None, None]:
    """Independent TestClient pre-authenticated as User A."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"Authorization": f"Bearer {user_a_token}"}) as client_a:
        yield client_a
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client_b(db_session: Session, user_b_token: str) -> Generator[TestClient, None, None]:
    """Independent TestClient pre-authenticated as User B."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"Authorization": f"Bearer {user_b_token}"}) as client_b:
        yield client_b
    app.dependency_overrides.clear()
