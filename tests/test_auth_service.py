import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.auth import hash_password, register_user, verify_password


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)


def test_register_user_success(db):
    user = register_user(db, "alice", "password123")
    assert user.id is not None
    assert user.username == "alice"
    assert user.hashed_password != "password123"


def test_register_user_duplicate_raises(db):
    register_user(db, "alice", "password123")
    with pytest.raises(ValueError, match="already taken"):
        register_user(db, "alice", "otherpassword")
