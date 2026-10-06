"""
Line-level discount allocation and tax computation service.
Implements the largest-remainder (Hare-Niemeyer) method in paise for gap-free discount distribution.
All math strictly guarantees the fundamental invariant:
    total_taxable + total_tax == grand_total (to the exact cent/paisa).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .gst_calculator import TWO_PLACES, ZERO_RUPEES, extract_tax, split_tax


@dataclass(frozen=True)
class AllocatedLine:
    line_index: int
    quantity: int
    unit_price_incl: Decimal
    rate: Decimal
    subtotal: Decimal
    discount_share: Decimal
    net_amount: Decimal
    taxable_value: Decimal
    tax_amount: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal


@dataclass(frozen=True)
class OrderTaxAllocation:
    lines: list[AllocatedLine]
    items_subtotal: Decimal
    discount_amount: Decimal
    items_net_total: Decimal
    highest_rate: Decimal
    shipping_fee: Decimal
    shipping_taxable: Decimal
    shipping_tax: Decimal
    shipping_cgst: Decimal
    shipping_sgst: Decimal
    shipping_igst: Decimal
    cod_fee: Decimal
    cod_taxable: Decimal
    cod_tax: Decimal
    cod_cgst: Decimal
    cod_sgst: Decimal
    cod_igst: Decimal
    total_taxable_value: Decimal
    total_tax_amount: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    grand_total: Decimal


def allocate_order_lines(
    lines: list[dict[str, Any]],
    discount_total: Decimal = ZERO_RUPEES,
    shipping_fee: Decimal = ZERO_RUPEES,
    cod_fee: Decimal = ZERO_RUPEES,
    intra_state: bool = True,
    registered: bool = True,
) -> OrderTaxAllocation:
    """
    Distribute an order-level discount proportionally across lines and extract GST.
    Mixed supply policy: Shipping and COD fees are taxed at the highest GST rate
    among all line items. (UNVERIFIED - confirm with accountant).
    """
    if not lines:
        return OrderTaxAllocation(
            lines=[],
            items_subtotal=ZERO_RUPEES,
            discount_amount=ZERO_RUPEES,
            items_net_total=ZERO_RUPEES,
            highest_rate=Decimal("18.00"),
            shipping_fee=shipping_fee,
            shipping_taxable=shipping_fee,
            shipping_tax=ZERO_RUPEES,
            shipping_cgst=ZERO_RUPEES,
            shipping_sgst=ZERO_RUPEES,
            shipping_igst=ZERO_RUPEES,
            cod_fee=cod_fee,
            cod_taxable=cod_fee,
            cod_tax=ZERO_RUPEES,
            cod_cgst=ZERO_RUPEES,
            cod_sgst=ZERO_RUPEES,
            cod_igst=ZERO_RUPEES,
            total_taxable_value=shipping_fee + cod_fee,
            total_tax_amount=ZERO_RUPEES,
            total_cgst=ZERO_RUPEES,
            total_sgst=ZERO_RUPEES,
            total_igst=ZERO_RUPEES,
            grand_total=shipping_fee + cod_fee,
        )

    # 1. Compute individual line subtotals
    line_subtotals: list[Decimal] = []
    for line in lines:
        qty = int(line["quantity"])
        price = Decimal(str(line["unit_price_incl"])).quantize(TWO_PLACES)
        line_subtotals.append((price * qty).quantize(TWO_PLACES))

    items_subtotal = sum(line_subtotals, ZERO_RUPEES)

    # 2. Clamp discount so it cannot exceed items subtotal or fall below zero
    discount_total = max(ZERO_RUPEES, min(Decimal(str(discount_total)).quantize(TWO_PLACES), items_subtotal))

    # 3. Largest-remainder method in integer paise
    total_discount_paise = int(round(discount_total * 100))
    total_subtotal_paise = int(round(items_subtotal * 100))

    allocated_paise: list[int] = [0] * len(lines)

    if total_discount_paise > 0 and total_subtotal_paise > 0:
        base_shares: list[int] = []
        remainders: list[tuple[float, int]] = []

        for i, sub in enumerate(line_subtotals):
            sub_paise = int(round(sub * 100))
            exact_share = (sub_paise * total_discount_paise) / total_subtotal_paise
            base = int(exact_share)
            base_shares.append(base)
            remainders.append((exact_share - base, i))

        sum_base = sum(base_shares)
        shortfall = total_discount_paise - sum_base

        # Sort descending by remainder, with index tie-breaker
        remainders.sort(key=lambda item: (-item[0], item[1]))

        allocated_paise = list(base_shares)
        for k in range(shortfall):
            idx = remainders[k][1]
            allocated_paise[idx] += 1

    # 4. Allocate each line's tax and net
    allocated_lines: list[AllocatedLine] = []
    highest_rate = max((Decimal(str(line.get("rate", "18.00"))) for line in lines), default=Decimal("18.00"))

    for i, line in enumerate(lines):
        qty = int(line["quantity"])
        price = Decimal(str(line["unit_price_incl"])).quantize(TWO_PLACES)
        rate = Decimal(str(line.get("rate", "18.00")))
        subtotal = line_subtotals[i]
        line_discount = (Decimal(allocated_paise[i]) / Decimal("100")).quantize(TWO_PLACES)
        net_amount = subtotal - line_discount

        tax_amount = extract_tax(net_amount, rate, registered=registered)
        taxable_value = net_amount - tax_amount
        cgst, sgst, igst = split_tax(tax_amount, intra_state=intra_state)

        allocated_lines.append(
            AllocatedLine(
                line_index=i,
                quantity=qty,
                unit_price_incl=price,
                rate=rate,
                subtotal=subtotal,
                discount_share=line_discount,
                net_amount=net_amount,
                taxable_value=taxable_value,
                tax_amount=tax_amount,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
            )
        )

    # 5. Shipping fee taxation (mixed supply at highest rate)
    shipping_fee = Decimal(str(shipping_fee)).quantize(TWO_PLACES)
    shipping_tax = extract_tax(shipping_fee, highest_rate, registered=registered)
    shipping_taxable = shipping_fee - shipping_tax
    ship_cgst, ship_sgst, ship_igst = split_tax(shipping_tax, intra_state=intra_state)

    # 6. COD fee taxation (mixed supply at highest rate)
    cod_fee = Decimal(str(cod_fee)).quantize(TWO_PLACES)
    cod_tax = extract_tax(cod_fee, highest_rate, registered=registered)
    cod_taxable = cod_fee - cod_tax
    cod_cgst, cod_sgst, cod_igst = split_tax(cod_tax, intra_state=intra_state)

    # 7. Aggregate totals
    items_net_total = sum((l.net_amount for l in allocated_lines), ZERO_RUPEES)
    total_taxable_value = sum((l.taxable_value for l in allocated_lines), ZERO_RUPEES) + shipping_taxable + cod_taxable
    total_tax_amount = sum((l.tax_amount for l in allocated_lines), ZERO_RUPEES) + shipping_tax + cod_tax

    total_cgst = sum((l.cgst for l in allocated_lines), ZERO_RUPEES) + ship_cgst + cod_cgst
    total_sgst = sum((l.sgst for l in allocated_lines), ZERO_RUPEES) + ship_sgst + cod_sgst
    total_igst = sum((l.igst for l in allocated_lines), ZERO_RUPEES) + ship_igst + cod_igst

    grand_total = items_net_total + shipping_fee + cod_fee

    return OrderTaxAllocation(
        lines=allocated_lines,
        items_subtotal=items_subtotal,
        discount_amount=discount_total,
        items_net_total=items_net_total,
        highest_rate=highest_rate,
        shipping_fee=shipping_fee,
        shipping_taxable=shipping_taxable,
        shipping_tax=shipping_tax,
        shipping_cgst=ship_cgst,
        shipping_sgst=ship_sgst,
        shipping_igst=ship_igst,
        cod_fee=cod_fee,
        cod_taxable=cod_taxable,
        cod_tax=cod_tax,
        cod_cgst=cod_cgst,
        cod_sgst=cod_sgst,
        cod_igst=cod_igst,
        total_taxable_value=total_taxable_value,
        total_tax_amount=total_tax_amount,
        total_cgst=total_cgst,
        total_sgst=total_sgst,
        total_igst=total_igst,
        grand_total=grand_total,
    )
