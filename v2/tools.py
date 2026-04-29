"""
HR tool implementations for the Responses API agent.

Defines three typed function tools that the model can call to answer
HR-related queries, together with the JSON schemas (``TOOL_SCHEMAS``) and
dispatch table (``TOOL_DISPATCH``) consumed by ``agent.py``.

The employee DataFrame is loaded once at module import time from the CSV path
resolved via the ``EMPLOYEE_CSV_PATH`` environment variable (defaults to
``employee_data.csv`` in the same directory as this file). Streamlit caches imported
modules per worker process, so the CSV is not re-read on every user message.

Tools
-----
get_employee_record(name)
    Full employee record lookup by name.
list_direct_reports(supervisor_name)
    Org-chart query returning all direct reports of a given supervisor.
compute_leave_encashment_value(name, days_to_encash)
    Peso value calculation using the HR policy formula:
    ``basic_pay_in_php / 30 * days_to_encash``.
"""

import json
import os
import pandas as pd
from pathlib import Path

_csv_path = os.getenv("EMPLOYEE_CSV_PATH", str(Path(__file__).parent / "employee_data.csv"))
_df = pd.read_csv(_csv_path)


def get_employee_record(name: str) -> dict:
    """Return the full HR record for an employee by name (case-insensitive).

    Args:
        name: Full name of the employee, e.g. ``"Alexander Verdad"``.

    Returns:
        A dict with all CSV columns as keys — ``employee_id``, ``name``,
        ``position``, ``organizational_unit``, ``rank``, ``hire_date``,
        ``regularization_date``, ``vacation_leave``, ``sick_leave``,
        ``basic_pay_in_php``, ``employment_status``, ``supervisor`` — or
        ``{"error": "..."}`` if no matching employee is found.
    """
    row = _df[_df["name"].str.lower() == name.lower()]
    if row.empty:
        return {"error": f"No employee found with name '{name}'"}
    return row.iloc[0].to_dict()


def list_direct_reports(supervisor_name: str) -> list:
    """Return all employees whose supervisor column matches the given name.

    Args:
        supervisor_name: Full name of the supervisor, e.g. ``"Joseph Santos"``.

    Returns:
        A list of dicts, each containing ``name``, ``position``, and ``rank``
        for one direct report. Returns an empty list if no reports are found.
    """
    reports = _df[_df["supervisor"].str.lower() == supervisor_name.lower()]
    if reports.empty:
        return []
    return reports[["name", "position", "rank"]].to_dict(orient="records")


def compute_leave_encashment_value(name: str, days_to_encash: int) -> dict:
    """Calculate the peso value of encashing unused leave days for an employee.

    Applies the HR policy formula: ``basic_pay_in_php / 30 * days_to_encash``.
    This matches the encashment rate defined in the HR policy for both Vacation
    Leave and Service Incentive Leave (Sick Leave cannot be encashed per policy).

    Args:
        name: Full name of the employee.
        days_to_encash: Number of unused leave days to convert to cash.

    Returns:
        A dict with keys ``basic_pay_in_php`` (float), ``days_to_encash``
        (int), and ``encashment_value_php`` (float, rounded to 2 decimal
        places), or ``{"error": "..."}`` if the employee is not found.
    """
    row = _df[_df["name"].str.lower() == name.lower()]
    if row.empty:
        return {"error": f"No employee found with name '{name}'"}
    basic_pay = float(row.iloc[0]["basic_pay_in_php"])
    # policy formula: basic_pay / 30 * days_to_encash
    value = basic_pay / 30 * days_to_encash
    return {
        "basic_pay_in_php": basic_pay,
        "days_to_encash": days_to_encash,
        "encashment_value_php": round(value, 2),
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_employee_record",
        "description": (
            "Look up a single employee's full record from the HR database. "
            "Returns position, rank, leave balances (vacation_leave, sick_leave), "
            "basic_pay_in_php, employment_status, supervisor, and hire dates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the employee, e.g. 'Alexander Verdad'",
                }
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "list_direct_reports",
        "description": (
            "Return a list of employees who report directly to the given supervisor. "
            "Each entry includes name, position, and rank."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "supervisor_name": {
                    "type": "string",
                    "description": "Full name of the supervisor, e.g. 'Joseph Santos'",
                }
            },
            "required": ["supervisor_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "compute_leave_encashment_value",
        "description": (
            "Calculate the peso value of encashing unused leave days for an employee. "
            "Uses the HR policy formula: basic_pay_in_php / 30 * days_to_encash."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the employee",
                },
                "days_to_encash": {
                    "type": "integer",
                    "description": "Number of leave days to encash",
                },
            },
            "required": ["name", "days_to_encash"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

TOOL_DISPATCH = {
    "get_employee_record": get_employee_record,
    "list_direct_reports": list_direct_reports,
    "compute_leave_encashment_value": compute_leave_encashment_value,
}


def dispatch(name: str, arguments_json: str) -> str:
    """Look up and call a tool by name, returning its result as a JSON string.

    Used by the agent loop to execute function calls emitted by the model.
    Errors from unknown tool names or bad arguments are caught and returned as
    ``{"error": "..."}`` JSON so the model can handle them gracefully rather
    than crashing the agent loop.

    Args:
        name: The function name as declared in ``TOOL_SCHEMAS`` and
            ``TOOL_DISPATCH``.
        arguments_json: JSON-encoded keyword arguments produced by the model,
            e.g. ``'{"name": "Alexander Verdad"}'``.

    Returns:
        JSON-encoded result string ready to be sent back as a
        ``function_call_output`` input item.
    """
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        args = json.loads(arguments_json)
        result = fn(**args)
        return json.dumps(result, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})
