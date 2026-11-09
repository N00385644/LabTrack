"""Pruebas de HU-02: catÃ¡logo y filtrado de equipos."""

from __future__ import annotations

from sqlalchemy import delete

from app.models import Equipment

from .helpers import login


def test_catalog_shows_required_fields(client):
    login(client)
    response = client.get("/catalog")
    assert response.status_code == 200
    assert "Laptop Dell Latitude 5440" in response.text
    assert "COMP-001" in response.text
    assert "CÃ³mputo" in response.text
    assert "Disponible" in response.text


def test_catalog_lists_all_categories(client):
    login(client)
    response = client.get("/catalog")
    for category in ("CÃ³mputo", "ElectrÃ³nica", "Redes"):
        assert category in response.text
    assert response.text.count("Reservar equipo") == 18


def test_filter_computo_only_shows_computo(client):
    login(client)
    response = client.get("/catalog?category=CÃ³mputo")
    assert response.status_code == 200
    assert "Laptop Dell Latitude 5440" in response.text
    assert "Osciloscopio Tektronix" not in response.text
    assert "Router Cisco 2911" not in response.text
    assert response.text.count("Reservar equipo") == 6


def test_filter_electronica_only_shows_electronica(client):
    login(client)
    response = client.get("/catalog?category=ElectrÃ³nica")
    assert "Osciloscopio Tektronix" in response.text
    assert "Laptop Dell Latitude 5440" not in response.text
    assert "Router Cisco 2911" not in response.text
    assert response.text.count("Reservar equipo") == 6


def test_filter_redes_only_shows_redes(client):
    login(client)
    response = client.get("/catalog?category=Redes")
    assert "Router Cisco 2911" in response.text
    assert "Switch Cisco Catalyst 2960" in response.text
    assert "Laptop Dell Latitude 5440" not in response.text
    assert response.text.count("Reservar equipo") == 6


def test_filter_without_results_shows_exact_message(client, db):
    login(client)
    db.execute(delete(Equipment).where(Equipment.category == "Redes"))
    db.commit()
    response = client.get("/catalog?category=Redes")
    assert response.status_code == 200
    assert "No hay equipos disponibles en esta categorÃ­a" in response.text
    assert "Ver todo el catÃ¡logo" in response.text


def test_invalid_category_ignores_filter(client):
    login(client)
    response = client.get("/catalog?category=Inexistente")
    assert response.status_code == 200
    assert response.text.count("Reservar equipo") == 18
    assert "Todos" in response.text


def test_catalog_escapes_untrusted_equipment_name(client, db):
    login(client)
    db.add(
        Equipment(
            name="<script>alert('xss')</script>",
            inventory_code="XSS-001",
            category="CÃ³mputo",
            description="Equipo de prueba",
        )
    )
    db.commit()
    response = client.get("/catalog")
    assert "<script>alert('xss')</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_borrowed_equipment_is_shown_but_not_reservable(client, db):
    login(client)
    equipment = db.query(Equipment).filter(Equipment.inventory_code == "COMP-001").one()
    equipment.status = "Prestado"
    db.commit()
    response = client.get("/catalog")
    assert "No disponible" in response.text
    assert "Reservar equipo" not in response.text.split("COMP-001", 1)[1].split("</article>", 1)[0]


def test_catalog_requires_authentication(client):
    response = client.get("/catalog", follow_redirects=False)
    assert response.status_code == 303
