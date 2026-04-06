from app.tools.schemas import ToolSpec
from app.tools.travel_tools import (
    escalate_to_human,
    estimate_stay_budget,
    get_exchange_rate,
    search_destination_tips,
    sum_expenses,
    validate_flight_request,
)


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="get_exchange_rate",
        description="Quy doi tien te voi du lieu mock. Input: from_currency, to_currency, amount.",
        parameters_schema={"type": "object", "required": ["from_currency", "to_currency", "amount"]},
        handler=get_exchange_rate,
        timeout_seconds=5,
    ),
    ToolSpec(
        name="estimate_stay_budget",
        description="Uoc tinh chi phi luu tru. Input: city, nights, comfort.",
        parameters_schema={"type": "object", "required": ["city", "nights", "comfort"]},
        handler=estimate_stay_budget,
        timeout_seconds=5,
    ),
    ToolSpec(
        name="sum_expenses",
        description="Tong hop chi phi tu danh sach item amount_vnd.",
        parameters_schema={"type": "object", "required": ["items"]},
        handler=sum_expenses,
        timeout_seconds=3,
    ),
    ToolSpec(
        name="validate_flight_request",
        description="Kiem tra input chuyen bay IATA va ngay khoi hanh.",
        parameters_schema={"type": "object", "required": ["origin_iata", "dest_iata", "departure_date"]},
        handler=validate_flight_request,
        timeout_seconds=3,
    ),
    ToolSpec(
        name="search_destination_tips",
        description="Lay goi y du lich theo city/query tu mock dataset.",
        parameters_schema={"type": "object", "required": []},
        handler=search_destination_tips,
        timeout_seconds=3,
    ),
    ToolSpec(
        name="escalate_to_human",
        description="Chuyen tiep ho tro vien (mock) khi ngoai pham vi hoac rui ro.",
        parameters_schema={"type": "object", "required": ["reason"]},
        handler=escalate_to_human,
        timeout_seconds=2,
    ),
]


def get_tool(name: str) -> ToolSpec | None:
    for tool in TOOLS:
        if tool.name == name:
            return tool
    return None
