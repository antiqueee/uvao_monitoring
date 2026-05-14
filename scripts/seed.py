from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Network, User, UserRole
from app.security import hash_password

NETWORK_NAMES = ["Капотня", "Выхино-Жулебино", "Марьино", "Кузьминки", "Люблино"]
DISTRICT_USERS = {
    "lublino": "Люблино",
    "kapotnya": "Капотня",
    "maryino": "Марьино",
    "vykhino": "Выхино-Жулебино",
    "kuzminki": "Кузьминки",
}


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        networks_by_name: dict[str, Network] = {}
        for name in NETWORK_NAMES:
            exists = db.scalar(select(Network).where(Network.name == name))
            if not exists:
                exists = Network(name=name)
                db.add(exists)
                db.flush()
            networks_by_name[name] = exists

        admin = db.scalar(select(User).where(User.login == settings.bootstrap_admin_login))
        if not admin:
            db.add(
                User(
                    login=settings.bootstrap_admin_login,
                    password_hash=hash_password(settings.bootstrap_admin_password),
                    display_name="Администратор",
                    role=UserRole.admin,
                )
            )
        for login, network_name in DISTRICT_USERS.items():
            exists = db.scalar(select(User).where(User.login == login))
            if not exists:
                db.add(
                    User(
                        login=login,
                        password_hash=hash_password(settings.bootstrap_admin_password),
                        display_name=network_name,
                        role=UserRole.user,
                        network_id=networks_by_name[network_name].id,
                    )
                )
        db.commit()


if __name__ == "__main__":
    main()
