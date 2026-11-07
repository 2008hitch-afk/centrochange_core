"""Pure, signed-cent projection of the operational receipt register.

No accounting payments are combined with operational receipts here.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import json


def summarize(sessions, receipts, start, end):
    first, last = date.fromisoformat(str(start)), date.fromisoformat(str(end))
    if last < first:
        raise ValueError('Invalid report period')
    allocation = {}
    period_cents = 0
    period_allocation = {}
    for receipt in receipts:
        when = date.fromisoformat(str(receipt['receipt_date'])[:10])
        entries = receipt['allocations']
        entries = json.loads(entries) if isinstance(entries, str) else entries
        if not isinstance(entries, list):
            raise ValueError('Invalid receipt allocations')
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError('Invalid receipt allocation')
            amount, appointment = item.get('cents'), item.get('appointment')
            if not isinstance(amount, int) or isinstance(amount, bool) or not appointment:
                raise ValueError('Invalid receipt allocation')
            allocation[appointment] = allocation.get(appointment, 0) + amount
            if first <= when <= last:
                period_cents += amount
                period_allocation[appointment] = period_allocation.get(appointment, 0) + amount
    result = {}
    for session in sessions:
        name = session['name']
        currency, economic = session.get('cc_currency_snapshot'), session.get('cc_economic_state')
        if currency not in ('EUR', None, ''):
            raise ValueError('Currency requires a separate report')
        raw = session.get('cc_price_snapshot')
        try:
            price = Decimal(str(raw)) if raw is not None else None
            if price is not None and (not price.is_finite() or price < 0 or price != price.quantize(Decimal('.01'))):
                raise ValueError('Invalid session price')
        except (InvalidOperation, TypeError) as exc:
            raise ValueError('Invalid session price') from exc
        cents = int(price * 100) if price is not None else None
        paid = allocation.get(name, 0)
        if paid < 0 or (cents is not None and paid > cents):
            raise ValueError('Inconsistent receipt allocation')
        if economic in ('Non Due', 'Waived', 'Package Covered') or cents == 0:
            status, remaining = 'Non dovuto', 0
        elif economic != 'Due' or cents is None:
            status, remaining = 'Da definire', None
        elif session.get('cc_paid') and not paid:
            # Historical paid facts without a receipt do not imply a dated receipt.
            status, remaining, paid = 'Saldata', 0, None
        else:
            remaining = cents - paid
            status = 'Saldata' if remaining == 0 else 'Parziale' if paid else 'Da incassare'
        if status == 'Da incassare' and (session.get('category') == 'future' or session.get('cc_classified_future')):
            status, remaining = 'In programma', 0
        result[name] = {'state': status, 'remaining_cents': remaining, 'allocated_cents': paid,
                        'period_cash_cents': period_allocation.get(name, 0)}
    counts = {name: 0 for name in ('Saldata', 'Parziale', 'Da incassare', 'Non dovuto', 'Da definire', 'In programma')}
    for row in result.values():
        counts[row['state']] += 1
    return {'cash_cents': period_cents, 'sessions': result, 'state_counts': counts,
            'session_remaining_cents': (None if any(row['remaining_cents'] is None for row in result.values())
                                        else sum(row['remaining_cents'] for row in result.values()))}
