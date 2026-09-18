from __future__ import annotations

import re


def bearer_header(access_token: str) -> dict:
    """Erzeugt Header für Bearer-Token-Authentifizierung"""
    return {"Authorization": f"Bearer {access_token}"}


def first_evse_from_coordinator(coord) -> dict | None:
    """Gib die erste (bevorzugt verfügbare) Wallbox aus coord.data zurück."""
    if not coord or not getattr(coord, "data", None):
        return None
    evses = coord.data.get("evse") or []
    if not evses:
        return None
    for wb in evses:
        if wb.get("available"):
            return wb
    return evses[0]  # Fallback: erste, auch wenn offline


def _split_camel(text: str) -> str:
    """'ChargingNormal' -> 'Charging Normal'."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text or "").strip()


def parse_wallbox_state(raw: str) -> tuple[str | None, str | None]:
    """Parse the KSEM REST ``state`` string into (main, sub) display strings.

    The KSEM e-mobility API returns a compound camelCase value of the form
    ``state<Main>SubState<Sub>`` (the ``SubState<Sub>`` part is optional).

    Examples:
        ``stateChargingSubStateChargingNormal`` -> ("Charging", "Charging Normal")
        ``stateFinishedSubStateChargingEnabled`` -> ("Finished", "Charging Enabled")
        ``stateOffline`` -> ("Offline", None)
        ``""`` -> (None, None)
    """
    if not raw:
        return (None, None)
    body = raw[5:] if raw.startswith("state") else raw
    if "SubState" in body:
        main, _, sub = body.partition("SubState")
    else:
        main, sub = body, ""
    return (_split_camel(main) or None, _split_camel(sub) or None)
