import json
import os
import pandas as pd
from pathlib import Path

_csv_path = os.getenv("EMPLOYEE_CSV_PATH", str(Path(__file__).parent.parent / "employee_data.csv"))
_df = pd.read_csv(_csv_path)


def get_employee_record(name: str) -> dict:
    row = _df[_df["name"].str.lower() == name.lower()]
    if row.empty:
        return {"error": f"No employee found with name '{name}'"}
    return row.iloc[0].to_dict()


def list_direct_reports(supervisor_name: str) -> list:
    reports = _df[_df["supervisor"].str.lower() == supervisor_name.lower()]
    if reports.empty:
        return []
    return reports[["name", "position", "rank"]].to_dict(orient="records")


def compute_leave_encashment_value(name: str, days_to_encash: int) -> dict:
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
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        args = json.loads(arguments_json)
        result = fn(**args)
        return json.dumps(result, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})
