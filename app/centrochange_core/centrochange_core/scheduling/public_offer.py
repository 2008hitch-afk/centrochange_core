"""Pure public-offer policy: only a real 20-minute, zero-priced initial meeting.

The public UI MUST NOT infer the mode from a director's current route or a
Fresha composite service. An operator must explicitly configure TWO distinct
Appointment Types in site-local configuration, then the live catalog is checked
again by the protected server API. This module is independently unit-testable.
"""
from decimal import Decimal, InvalidOperation

MODES = ("sede", "online")
DURATION = 20


class PublicOfferError(ValueError):
    pass


def configured_type(mapping, mode):
    if mode not in MODES:
        raise PublicOfferError("Modalità di prenotazione non consentita.")
    if not isinstance(mapping, dict):
        raise PublicOfferError("Modalità di prenotazione non configurate.")
    names = [mapping.get(name) for name in MODES]
    if any(not isinstance(name, str) or not name.strip() or len(name) > 140 for name in names):
        raise PublicOfferError("I due servizi pubblici devono essere configurati.")
    if names[0].strip() == names[1].strip():
        raise PublicOfferError("Le modalità richiedono servizi distinti.")
    return mapping[mode].strip()


def validate_free_offer(profile, mode):
    if mode not in MODES:
        raise PublicOfferError('Modalità non consentita.')
    try:
        duration = Decimal(str(profile["duration"]))
        price = Decimal(str(profile["cc_price_snapshot"]))
    except (TypeError, ValueError, KeyError, InvalidOperation) as exc:
        raise PublicOfferError("Il primo colloquio non è configurato correttamente.") from exc
    if not duration.is_finite() or duration != DURATION or not price.is_finite() or price != 0:
        raise PublicOfferError("Il primo colloquio deve durare 20 minuti ed essere gratuito.")
    if profile.get("cc_currency_snapshot") != "EUR":
        raise PublicOfferError("La valuta del colloquio gratuito non è configurata.")
    label = profile.get("cc_service_label")
    if not isinstance(label, str):
        raise PublicOfferError("Il servizio pubblico non ha una descrizione valida.")
    canonical = label.casefold()
    if (mode == "sede" and "sede" not in canonical) or (
        mode == "online" and not any(word in canonical for word in ("online", "on-line", "a distanza"))
    ):
        raise PublicOfferError("Il servizio non distingue la modalità scelta.")
    return True
