from unittest.mock import Mock

import pytest

from shop.cart import Cart

# ---------- add / items_count ----------


def test_new_cart_is_empty(empty_cart: Cart) -> None:
    assert empty_cart.items_count() == 0
    assert empty_cart.total() == 0.0


def test_add_default_qty_is_one(empty_cart: Cart) -> None:
    empty_cart.add("book", price=200.0)
    assert empty_cart.items_count() == 1


def test_items_count(cart_with_items: Cart) -> None:
    assert cart_with_items.items_count() == 6


def test_add_same_name_increases_qty(cart_with_items: Cart) -> None:
    cart_with_items.add("book", price=200.0, qty=3)
    assert cart_with_items.items_count() == 9
    assert cart_with_items.total() == 1060.0


def test_add_same_name_different_price_keeps_first_price(empty_cart: Cart) -> None:
    # Рішення: ціна фіксується при першому додаванні, повторне додавання лише збільшує qty.
    empty_cart.add("book", price=200.0)
    empty_cart.add("book", price=999.0)
    assert empty_cart.items_count() == 2
    assert empty_cart.total() == 400.0


def test_add_zero_price_is_allowed(empty_cart: Cart) -> None:
    empty_cart.add("gift", price=0.0)
    assert empty_cart.items_count() == 1
    assert empty_cart.total() == 0.0


def test_add_negative_price_raises(empty_cart: Cart) -> None:
    with pytest.raises(ValueError, match="price"):
        empty_cart.add("book", price=-1.0)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_non_positive_qty_raises(empty_cart: Cart, qty: int) -> None:
    with pytest.raises(ValueError, match="qty"):
        empty_cart.add("book", price=10.0, qty=qty)


# ---------- remove ----------


def test_remove_item(cart_with_items: Cart) -> None:
    cart_with_items.remove("pen")
    assert cart_with_items.items_count() == 2
    assert cart_with_items.total() == 400.0


def test_remove_missing_item_raises(empty_cart: Cart) -> None:
    with pytest.raises(KeyError):
        empty_cart.remove("ghost")


# ---------- total ----------


def test_total_without_discount(cart_with_items: Cart) -> None:
    assert cart_with_items.total() == 460.0


@pytest.mark.parametrize(
    ("discount", "expected"),
    [(0, 400.0), (10, 360.0), (50, 200.0), (99.5, 2.0), (100, 0.0)],
)
def test_discounts_boundaries(empty_cart: Cart, discount: float, expected: float) -> None:
    empty_cart.add("book", price=200.0, qty=2)
    assert empty_cart.total(discount_percent=discount) == expected


@pytest.mark.parametrize("discount", [-0.01, -10, 100.01, 150])
def test_invalid_discount_raises(empty_cart: Cart, discount: float) -> None:
    with pytest.raises(ValueError, match="discount_percent"):
        empty_cart.total(discount_percent=discount)


def test_total_float_rounding(empty_cart: Cart) -> None:
    empty_cart.add("a", price=0.1)
    empty_cart.add("b", price=0.2)
    assert empty_cart.total() == pytest.approx(0.3)


# ---------- total_in (тестовий дублер RateProvider) ----------


def test_total_in_usd_with_mock() -> None:
    rates = Mock()
    rates.get_rate.return_value = 40.0  # 1 USD = 40 UAH
    cart = Cart()
    cart.add("book", price=400.0)
    assert cart.total_in("USD", rates) == 10.0
    rates.get_rate.assert_called_once_with("USD")


class FixedRates:
    """Заглушка (stub) замість реального сервісу курсів."""

    def __init__(self, rates: dict[str, float]) -> None:
        self._rates = rates

    def get_rate(self, currency: str) -> float:
        return self._rates[currency]


def test_total_in_eur_with_stub(cart_with_items: Cart) -> None:
    rates = FixedRates({"EUR": 46.0})
    assert cart_with_items.total_in("EUR", rates) == 10.0


@pytest.mark.parametrize("bad_rate", [0.0, -40.0])
def test_total_in_non_positive_rate_raises(cart_with_items: Cart, bad_rate: float) -> None:
    rates = Mock()
    rates.get_rate.return_value = bad_rate
    with pytest.raises(ValueError, match="rate"):
        cart_with_items.total_in("USD", rates)


# ---------- most_expensive (TDD) ----------


def test_most_expensive_empty_cart_returns_none(empty_cart: Cart) -> None:
    assert empty_cart.most_expensive() is None


def test_most_expensive_by_unit_price(cart_with_items: Cart) -> None:
    item = cart_with_items.most_expensive()
    assert item is not None
    assert item.name == "book"


def test_most_expensive_ignores_quantity(empty_cart: Cart) -> None:
    # pen: 15 * 100 = 1500 у сумі, але дорожча за одиницю — book
    empty_cart.add("pen", price=15.0, qty=100)
    empty_cart.add("book", price=200.0, qty=1)
    item = empty_cart.most_expensive()
    assert item is not None
    assert item.name == "book"


def test_most_expensive_single_item(empty_cart: Cart) -> None:
    empty_cart.add("pen", price=15.0)
    item = empty_cart.most_expensive()
    assert item is not None
    assert item.price == 15.0
