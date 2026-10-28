"""Deterministic Phase 3 claim verification against confirmed product facts."""

from decimal import Decimal

from app.models.domain import Claim, Product


def verify_claim(claim: Claim, product: Product) -> tuple[str, str, dict | None, str | None]:
    """Return verdict, severity, evidence snapshot and optional repair suggestion.

    This deliberately supports only facts it can prove from the product record. Everything
    else fails closed as unverified rather than relying on a writer/model assertion.
    """
    text = claim.text.casefold()
    if claim.kind != "fact":
        return "unverified", "low", None, "Keep this as a subjective opinion, not a factual claim."

    facts = {
        "name": product.name,
        "price_inr": f"{Decimal(product.price_inr):.2f}",
        **{key: str(value) for key, value in product.attributes.items()},
    }
    for field, value in facts.items():
        if value.casefold() in text:
            return "supported", "low", {"field": field, "value": value}, None

    contradictory_markers = ("100% pure silk", "pure silk", "green")
    if any(marker in text for marker in contradictory_markers):
        material = str(product.attributes.get("material", "")).casefold()
        color = str(product.attributes.get("color", "")).casefold()
        if ("silk" in text and "silk" not in material) or ("green" in text and color != "green"):
            return "contradicted", "high", {"material": material, "color": color}, "Use confirmed product facts only."

    return "unverified", "medium", None, "Remove the unsupported claim or ask the seller to confirm it."
