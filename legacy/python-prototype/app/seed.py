"""Datos iniciales de demostración para LabTrack."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config
from .database import Base, build_engine, build_session_factory
from .models import Equipment, Reservation, User
from .security import hash_password

DEMO_STUDENT = ("20240001", "Valeria Ramos Quispe", "Estudiante2026!")
ADMIN = ("ADMIN01", "Carlos Mendoza Ríos", "Admin2026!")
EXTRA_STUDENTS = [
    ("20240002", "Diego Fernández Soto"),
    ("20240003", "Camila Torres Vega"),
]
LOAD_PASSWORD = "Carga2026!"

EQUIPMENT = [
    ("Laptop Dell Latitude 5440", "COMP-001", "Cómputo", "Laptop i7, 16 GB RAM, 512 GB SSD", "Laboratorio de Cómputo A"),
    ("Workstation HP Z2 G9", "COMP-002", "Cómputo", "Estación de trabajo para diseño y simulación", "Laboratorio de Cómputo A"),
    ("Monitor LG UltraFine 27\"", "COMP-003", "Cómputo", "Monitor 4K con conexión USB-C", "Laboratorio de Cómputo A"),
    ("Laptop Lenovo ThinkPad E14", "COMP-004", "Cómputo", "Laptop para desarrollo de software", "Laboratorio de Cómputo B"),
    ("MacBook Air M2", "COMP-005", "Cómputo", "Equipo para desarrollo móvil", "Laboratorio de Cómputo B"),
    ("Teclado mecánico Logitech MX", "COMP-006", "Cómputo", "Teclado inalámbrico para prácticas", "Laboratorio de Cómputo B"),
    ("Osciloscopio Tektronix TBS1052B", "ELEC-001", "Electrónica", "Osciloscopio digital de 2 canales, 50 MHz", "Laboratorio de Electrónica"),
    ("Multímetro Fluke 87V", "ELEC-002", "Electrónica", "Multímetro industrial True RMS", "Laboratorio de Electrónica"),
    ("Fuente de alimentación DC", "ELEC-003", "Electrónica", "Fuente regulable 0-30 V / 5 A", "Laboratorio de Electrónica"),
    ("Generador de señales", "ELEC-004", "Electrónica", "Generador de funciones 2 MHz", "Laboratorio de Electrónica"),
    ("Kit Arduino Mega 2560", "ELEC-005", "Electrónica", "Kit de desarrollo con sensores y actuadores", "Laboratorio de Electrónica"),
    ("Raspberry Pi 5", "ELEC-006", "Electrónica", "Placa SBC para proyectos de IoT", "Laboratorio de Electrónica"),
    ("Router Cisco 2911", "RED-001", "Redes", "Router modular para prácticas de routing", "Laboratorio de Redes"),
    ("Switch Cisco Catalyst 2960", "RED-002", "Redes", "Switch administrable de 24 puertos", "Laboratorio de Redes"),
    ("Access Point Ubiquiti U6", "RED-003", "Redes", "Punto de acceso Wi-Fi 6", "Laboratorio de Redes"),
    ("Analizador de red Fluke LinkIQ", "RED-004", "Redes", "Tester de cables y certificación de red", "Laboratorio de Redes"),
    ("Patch panel 24 puertos", "RED-005", "Redes", "Panel de parcheo categoría 6", "Laboratorio de Redes"),
    ("Probador de cables RJ45", "RED-006", "Redes", "Tester de continuidad para cables de red", "Laboratorio de Redes"),
]


def seed_database(
    db: Session,
    include_load_users: bool = True,
    with_demo_reservations: bool = True,
) -> bool:
    """Carga datos solo si la base está vacía. Retorna True si sembró."""
    existing = db.scalar(select(func.count(User.id))) or 0
    if existing:
        return False

    users = [
        User(
            code=ADMIN[0],
            full_name=ADMIN[1],
            email="admin@labtrack.edu.pe",
            password_hash=hash_password(ADMIN[2]),
            role=config.ROLE_ADMIN,
        ),
        User(
            code=DEMO_STUDENT[0],
            full_name=DEMO_STUDENT[1],
            email="valeria.ramos@labtrack.edu.pe",
            password_hash=hash_password(DEMO_STUDENT[2]),
            role=config.ROLE_STUDENT,
        ),
    ]
    for code, name in EXTRA_STUDENTS:
        users.append(
            User(
                code=code,
                full_name=name,
                email=f"{code}@labtrack.edu.pe",
                password_hash=hash_password(DEMO_STUDENT[2]),
                role=config.ROLE_STUDENT,
            )
        )

    if include_load_users:
        for index in range(1, 61):
            code = f"2024{1000 + index:04d}"
            users.append(
                User(
                    code=code,
                    full_name=f"Estudiante de Carga {index:02d}",
                    email=f"{code}@labtrack.edu.pe",
                    password_hash=hash_password(LOAD_PASSWORD),
                    role=config.ROLE_STUDENT,
                )
            )
    db.add_all(users)

    equipment = [
        Equipment(
            name=name,
            inventory_code=inventory_code,
            category=category,
            description=description,
            location=location,
        )
        for name, inventory_code, category, description, location in EQUIPMENT
    ]
    db.add_all(equipment)
    db.flush()

    by_code = {item.inventory_code: item for item in equipment}
    students = {user.code: user for user in users}

    if with_demo_reservations:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        by_code["COMP-002"].status = config.EQUIPMENT_BORROWED
        by_code["RED-002"].status = config.EQUIPMENT_BORROWED

        db.add_all(
            [
                Reservation(
                    user_id=students["20240001"].id,
                    equipment_id=by_code["ELEC-001"].id,
                    date=tomorrow,
                    start_time=time(10, 0),
                    end_time=time(12, 0),
                    status=config.RES_PENDING,
                ),
                Reservation(
                    user_id=students["20240003"].id,
                    equipment_id=by_code["COMP-001"].id,
                    date=tomorrow,
                    start_time=time(14, 0),
                    end_time=time(16, 0),
                    status=config.RES_PENDING,
                ),
                Reservation(
                    user_id=students["20240002"].id,
                    equipment_id=by_code["COMP-002"].id,
                    date=today,
                    start_time=time(8, 0),
                    end_time=time(10, 0),
                    status=config.RES_APPROVED,
                    reviewed_by=ADMIN[1],
                    reviewed_at=datetime.now(),
                ),
                Reservation(
                    user_id=students["20240003"].id,
                    equipment_id=by_code["RED-002"].id,
                    date=tomorrow,
                    start_time=time(8, 0),
                    end_time=time(10, 0),
                    status=config.RES_APPROVED,
                    reviewed_by=ADMIN[1],
                    reviewed_at=datetime.now(),
                ),
                Reservation(
                    user_id=students["20240001"].id,
                    equipment_id=by_code["ELEC-002"].id,
                    date=yesterday,
                    start_time=time(10, 0),
                    end_time=time(12, 0),
                    status=config.RES_RETURNED,
                    reviewed_by=ADMIN[1],
                    reviewed_at=datetime.now() - timedelta(days=1),
                    returned_at=datetime.combine(yesterday, time(11, 45)),
                ),
            ]
        )

    db.commit()
    return True


def reset_database(database_url: str | None = None) -> None:
    url = database_url or config.get_database_url()
    if url.startswith("sqlite:///"):
        path = Path(url.replace("sqlite:///", ""))
        if path.exists():
            path.unlink()
    engine = build_engine(url)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as db:
        seed_database(db)
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicializa la base de datos de LabTrack")
    parser.add_argument("--reset", action="store_true", help="Elimina y recrea la base de datos")
    args = parser.parse_args()
    if args.reset:
        reset_database()
        print("Base de datos recreada con datos de demostración.")
    else:
        engine = build_engine(config.get_database_url())
        Base.metadata.create_all(engine)
        factory = build_session_factory(engine)
        with factory() as session:
            seeded = seed_database(session)
        print("Datos iniciales cargados." if seeded else "La base de datos ya contenía datos.")
