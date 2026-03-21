from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    PNAddressCatalog,
    PNAddressJobRule,
    PNAddressMeasurement,
    PNAddressPlant,
)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[,\.;:\-\(\)\[\]#]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _normalize_address_key(raw_address: str | None) -> str:
    return _normalize_text(raw_address)


def _extract_number(raw_address: str | None) -> str:
    text = raw_address or ""
    match = re.search(r"\b(\d+[a-zA-Z\-]*)\b", text)
    return match.group(1).strip().lower() if match else ""


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except Exception:
        return None


def _plant_sort_key(item: PNAddressPlant) -> tuple[int, int]:
    return (item.sort_order or 0, item.id or 0)


def _normalize_tipo_label(tipo: str | None) -> str:
    raw = (tipo or "").strip().lower()
    if not raw:
        return "item"
    if raw in {"janela", "janelas"}:
        return "janela"
    if raw in {"porta", "portas"}:
        return "porta"
    if raw in {"sacada", "sacadas"}:
        return "sacada"
    if raw in {"sacada_l", "sacada l", "sacada-l"}:
        return "sacada_L"
    return raw


def _pluralize_tipo(tipo: str, quantity: int) -> str:
    base = _normalize_tipo_label(tipo)

    if quantity <= 1:
        return base

    if base == "janela":
        return "janelas"
    if base == "porta":
        return "portas"
    if base == "sacada":
        return "sacadas"
    if base == "sacada_L":
        return "sacadas_L"

    if base.endswith("s"):
        return base
    return f"{base}s"


def _clean_descricao_for_tipo(tipo: str | None, descricao: str | None) -> str:
    desc = (descricao or "").strip()
    if not desc:
        return ""

    normalized_tipo = _normalize_tipo_label(tipo)

    if normalized_tipo == "sacada_L":
        desc = re.sub(r"^\s*sacada(?:[_\s-]*l)?\s*", "", desc, flags=re.I)
    else:
        desc = re.sub(rf"^\s*{re.escape(normalized_tipo)}s?\s*", "", desc, flags=re.I)

    desc = re.sub(r"\s+", " ", desc).strip(" -_,;")
    return desc


def _build_item_label(tipo: str | None, descricao: str | None, quantity: int = 1) -> str:
    tipo_base = _pluralize_tipo(tipo or "item", quantity)
    desc_clean = _clean_descricao_for_tipo(tipo, descricao)

    if desc_clean:
        return f"{tipo_base} {desc_clean}".strip()
    return tipo_base.strip()


@dataclass(slots=True)
class AddressMeasureItem:
    legacy_id: int
    endereco_id: int
    tipo: str
    descricao: str
    largura_m: float | None
    altura_m: float | None
    lado_a_m: float | None
    lado_b_m: float | None
    observacao: str
    planta: str | None

    def selection_id(self) -> str:
        return f"medida_{self.legacy_id}"

    def label(self) -> str:
        return _build_item_label(self.tipo, self.descricao, 1)

    def summary(self) -> str:
        base = self.label()
        if self.largura_m is not None and self.altura_m is not None:
            return f"{base} {self.largura_m:.2f} x {self.altura_m:.2f}"
        if self.lado_a_m is not None and self.lado_b_m is not None and self.altura_m is not None:
            return f"{base} {self.lado_a_m:.2f} x {self.lado_b_m:.2f} x {self.altura_m:.2f}"
        return base

    def to_quote_item_dict(self) -> dict[str, Any]:
        width = self.largura_m if self.largura_m is not None else self.lado_a_m
        height = self.altura_m if self.altura_m is not None else self.lado_b_m
        return {
            "legacy_id": self.legacy_id,
            "tipo": _normalize_tipo_label(self.tipo),
            "descricao": _clean_descricao_for_tipo(self.tipo, self.descricao),
            "width": width,
            "height": height,
            "lado_a_m": self.lado_a_m,
            "lado_b_m": self.lado_b_m,
            "observacao": (self.observacao or "").strip(),
            "planta": (self.planta or "").strip() or None,
            "source": "address_catalog",
        }


class AddressCatalog:
    def __init__(self, *, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def _get_full_catalog_row(self, catalog_id: int) -> PNAddressCatalog | None:
        stmt = (
            select(PNAddressCatalog)
            .where(
                PNAddressCatalog.company_id == self.company_id,
                PNAddressCatalog.id == catalog_id,
                PNAddressCatalog.is_active.is_(True),
            )
            .options(
                selectinload(PNAddressCatalog.plants),
                selectinload(PNAddressCatalog.measurements),
                selectinload(PNAddressCatalog.job_rules),
            )
        )
        return self.db.scalar(stmt)

    def _find_best_catalog_id(self, address_text: str) -> int | None:
        normalized = _normalize_address_key(address_text)
        if not normalized:
            return None

        number = _extract_number(address_text)

        stmt = (
            select(PNAddressCatalog.id, PNAddressCatalog.normalized_address)
            .where(
                PNAddressCatalog.company_id == self.company_id,
                PNAddressCatalog.is_active.is_(True),
            )
            .order_by(PNAddressCatalog.id.asc())
        )
        rows = list(self.db.execute(stmt).all())
        if not rows:
            return None

        if number:
            for row in rows:
                row_norm = row.normalized_address or ""
                if row_norm == normalized and re.search(rf"\b{re.escape(number)}\b", row_norm):
                    return int(row.id)

        for row in rows:
            row_norm = row.normalized_address or ""
            if row_norm == normalized:
                return int(row.id)

        if number:
            for row in rows:
                row_norm = row.normalized_address or ""
                if re.search(rf"\b{re.escape(number)}\b", row_norm):
                    return int(row.id)

        for row in rows:
            row_norm = row.normalized_address or ""
            if normalized in row_norm or row_norm in normalized:
                return int(row.id)

        return None

    def lookup_address(self, address_text: str) -> dict[str, Any]:
        if not address_text:
            return {
                "found": False,
                "endereco_id": None,
                "catalog_address_id": None,
                "address_text": "",
                "normalized_address": "",
                "items": [],
                "plants": {},
                "job_rules": [],
            }

        catalog_id = self._find_best_catalog_id(address_text)
        if not catalog_id:
            return {
                "found": False,
                "endereco_id": None,
                "catalog_address_id": None,
                "address_text": address_text,
                "normalized_address": _normalize_address_key(address_text),
                "items": [],
                "plants": {},
                "job_rules": [],
            }

        catalog = self._get_full_catalog_row(catalog_id)
        if catalog is None:
            return {
                "found": False,
                "endereco_id": None,
                "catalog_address_id": None,
                "address_text": address_text,
                "normalized_address": _normalize_address_key(address_text),
                "items": [],
                "plants": {},
                "job_rules": [],
            }

        plants_by_id = {
            plant.id: plant
            for plant in sorted(catalog.plants or [], key=_plant_sort_key)
            if plant.is_active
        }

        items: list[AddressMeasureItem] = []
        plants: dict[str, list[AddressMeasureItem]] = {}

        active_measurements = [m for m in (catalog.measurements or []) if m.is_active]
        active_measurements.sort(key=lambda m: (m.plant_id or 0, m.id))

        for measurement in active_measurements:
            plant = plants_by_id.get(measurement.plant_id) if measurement.plant_id else None
            plant_name = plant.name if plant else None

            item = AddressMeasureItem(
                legacy_id=int(measurement.id),
                endereco_id=int(catalog.id),
                tipo="janela",
                descricao=(measurement.label or "").strip(),
                largura_m=_to_float(measurement.width_m),
                altura_m=_to_float(measurement.height_m),
                lado_a_m=None,
                lado_b_m=None,
                observacao=(measurement.notes or "").strip(),
                planta=(plant_name or "").strip() or None,
            )
            items.append(item)
            if plant_name:
                plants.setdefault(plant_name, []).append(item)

        rules_payload: list[dict[str, Any]] = []
        for rule in catalog.job_rules or []:
            if not rule.is_active:
                continue
            rules_payload.append(
                {
                    "id": rule.id,
                    "plant_id": rule.plant_id,
                    "rule_type": rule.rule_type,
                    "rule_value": rule.rule_value,
                    "notes": rule.notes,
                }
            )

        return {
            "found": True,
            "endereco_id": catalog.id,
            "catalog_address_id": catalog.id,
            "address_text": catalog.raw_address,
            "normalized_address": catalog.normalized_address,
            "items": items,
            "plants": plants,
            "job_rules": rules_payload,
        }

    def load_job_rule_context(self, address_text: str) -> dict[str, Any]:
        lookup = self.lookup_address(address_text)
        if not lookup["found"]:
            return {"endereco_id": None, "job_rule": None, "job_rules": []}
        rules = lookup.get("job_rules") or []
        return {
            "endereco_id": lookup["endereco_id"],
            "job_rule": rules[0] if rules else None,
            "job_rules": rules,
        }


def _parse_decimal_pt(v: str) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    v = v.replace(" ", "").replace(",", ".")
    try:
        return float(v)
    except Exception:
        return None


def parse_manual_measurements_block(text: str) -> list[dict[str, Any]]:
    lines = []
    for raw in (text or "").splitlines():
        stripped = raw.strip()
        if stripped:
            lines.append(stripped)

    parsed: list[dict[str, Any]] = []

    for line in lines:
        s = re.sub(r"^\s*item\s*:\s*", "", line.strip(), flags=re.I)

        qty = 1
        qty_match = re.match(r"^\s*(\d+)\s*(.*)$", s)
        if qty_match:
            try:
                qty = max(1, int(qty_match.group(1)))
            except Exception:
                qty = 1
            s = qty_match.group(2).strip()

        tipo_match = None
        tipo = None

        tipo_match = re.search(r"\b(sacada[_\s-]*l)\b", s, flags=re.I)
        if tipo_match:
            tipo = "sacada_L"
        else:
            tipo_match = re.search(r"\b(sacada)\b", s, flags=re.I)
            if tipo_match:
                tipo = "sacada"
            else:
                tipo_match = re.search(r"\b(janela|janelas|porta|portas)\b", s, flags=re.I)
                if tipo_match:
                    tipo = _normalize_tipo_label(tipo_match.group(1))

        if not tipo or not tipo_match:
            continue

        rest = s[tipo_match.end():].strip()
        normalized_rest = rest.lower().replace("×", "x")
        numbers = re.findall(r"(\d+(?:[.,]\d+)?)", normalized_rest)

        if len(numbers) < 2:
            continue

        width = _parse_decimal_pt(numbers[-2])
        height = _parse_decimal_pt(numbers[-1])

        if width is None or height is None:
            continue

        desc = re.sub(r"\d+(?:[.,]\d+)?", " ", rest)
        desc = re.sub(r"[xX;]", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        desc = _clean_descricao_for_tipo(tipo, desc)

        parsed.append(
            {
                "legacy_id": None,
                "tipo": _normalize_tipo_label(tipo),
                "descricao": desc,
                "width": width,
                "height": height,
                "lado_a_m": None,
                "lado_b_m": None,
                "observacao": "",
                "planta": None,
                "quantity": qty,
                "source": "manual",
            }
        )

    return parsed


def format_measure_choice_title(item: dict[str, Any]) -> str:
    tipo = _normalize_tipo_label(item.get("tipo") or "item")
    descricao = _clean_descricao_for_tipo(tipo, item.get("descricao"))
    width = item.get("width")
    height = item.get("height")
    quantity = int(item.get("quantity") or 1)

    base = _build_item_label(tipo, descricao, quantity)

    if width is not None and height is not None:
        try:
            return f"{base} {float(width):.2f}x{float(height):.2f}"[:24]
        except Exception:
            return base[:24]

    return base[:24]
