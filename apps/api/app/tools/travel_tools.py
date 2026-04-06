from datetime import datetime
from typing import Any

from app.tools.schemas import ToolResult


MOCK_EXCHANGE_RATES = {
    ("USD", "VND"): 25000.0,
    ("VND", "USD"): 1 / 25000.0,
    ("EUR", "VND"): 27000.0,
}

MOCK_CITY_STAY = {
    "da lat": {"budget": 350000, "standard": 600000, "comfort": 1000000},
    "da nang": {"budget": 450000, "standard": 800000, "comfort": 1300000},
    "ha noi": {"budget": 500000, "standard": 900000, "comfort": 1500000},
}

MOCK_DESTINATION_TIPS = {
    "hoi an": [
        "Tham quan Pho co Hoi An vao buoi toi de ngam den long.",
        "Thu cao lau va banh mi Hoi An tai cac quan dia phuong.",
        "Di thuyen tren song Hoai vao buoi chieu muon.",
    ],
    "da lat": [
        "Di som de tranh ket xe o khu Ho Xuan Huong.",
        "Mang ao khoac mong vi nhiet do toi giam nhanh.",
        "Len lich tham quan theo cum de tiet kiem chi phi di chuyen.",
    ],
}


def get_exchange_rate(args: dict[str, Any]) -> ToolResult:
    # Tool quy doi tien te mock (currency conversion).
    from_currency = str(args.get("from_currency", "")).upper()
    to_currency = str(args.get("to_currency", "")).upper()
    amount = args.get("amount")

    try:
        amount_float = float(amount)
    except (TypeError, ValueError):
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="amount invalid")

    if amount_float <= 0:
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="amount <= 0")

    rate = MOCK_EXCHANGE_RATES.get((from_currency, to_currency))
    if rate is None:
        return ToolResult(
            ok=False,
            data="",
            error_code="BAD_PARAMS",
            message=f"unsupported pair {from_currency}/{to_currency}",
        )

    converted = amount_float * rate
    return ToolResult(
        ok=True,
        data=(
            f"Ty gia mock {from_currency}/{to_currency}: {rate:.4f}. "
            f"So tien quy doi: {converted:,.0f} {to_currency}."
        ),
    )


def estimate_stay_budget(args: dict[str, Any]) -> ToolResult:
    city = str(args.get("city", "")).strip().lower()
    comfort = str(args.get("comfort", "standard")).strip().lower()
    nights = args.get("nights", 1)

    try:
        nights_int = int(nights)
    except (TypeError, ValueError):
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="nights invalid")

    if nights_int < 1 or nights_int > 30:
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="nights out of range")

    city_price = MOCK_CITY_STAY.get(city)
    if not city_price or comfort not in city_price:
        return ToolResult(
            ok=False, data="", error_code="BAD_PARAMS", message="city/comfort unsupported"
        )

    nightly = city_price[comfort]
    total = nightly * nights_int
    return ToolResult(
        ok=True,
        data=f"Uoc tinh luu tru tai {city.title()} ({comfort}) trong {nights_int} dem: {total:,.0f} VND.",
    )


def sum_expenses(args: dict[str, Any]) -> ToolResult:
    items = args.get("items")
    if not isinstance(items, list) or not items:
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="items invalid")

    total = 0.0
    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="item invalid")
        label = str(item.get("label", "item"))
        amount = item.get("amount_vnd", 0)
        try:
            amount_float = float(amount)
        except (TypeError, ValueError):
            return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="amount invalid")
        total += amount_float
        lines.append(f"- {label}: {amount_float:,.0f} VND")

    return ToolResult(
        ok=True,
        data="Tong hop chi phi:\n" + "\n".join(lines) + f"\nTong cong: {total:,.0f} VND.",
    )


def validate_flight_request(args: dict[str, Any]) -> ToolResult:
    origin = str(args.get("origin_iata", "")).upper()
    dest = str(args.get("dest_iata", "")).upper()
    departure_date = str(args.get("departure_date", ""))

    if len(origin) != 3 or len(dest) != 3:
        return ToolResult(ok=False, data="", error_code="BAD_PARAMS", message="iata must be 3 chars")

    try:
        datetime.strptime(departure_date, "%Y-%m-%d")
    except ValueError:
        return ToolResult(
            ok=False,
            data="",
            error_code="INVALID_DATE",
            message="Ngay bay khong hop le, vui long dung dinh dang YYYY-MM-DD.",
        )

    return ToolResult(
        ok=True,
        data=f"Thong tin chuyen bay hop le: {origin} -> {dest} vao ngay {departure_date}.",
    )


def search_destination_tips(args: dict[str, Any]) -> ToolResult:
    city = str(args.get("city", "")).strip().lower()
    query = str(args.get("query", "")).strip().lower()
    key = city or query

    tips = MOCK_DESTINATION_TIPS.get(key)
    if not tips:
        tips = [
            "Uu tien lich trinh theo cum dia diem de tiet kiem thoi gian.",
            "Kiem tra thoi tiet va gio cao diem truoc khi di chuyen.",
            "Du tru 10-15% ngan sach cho chi phi phat sinh.",
        ]

    return ToolResult(ok=True, data="Goi y du lich:\n- " + "\n- ".join(tips))


def escalate_to_human(args: dict[str, Any]) -> ToolResult:
    reason = str(args.get("reason", "out_of_scope"))
    return ToolResult(
        ok=True,
        data=(
            "Da kich hoat chuyen tiep ho tro vien (mock). "
            f"Ly do: {reason}. Ma tham chieu: REF-MOCK-001."
        ),
    )
