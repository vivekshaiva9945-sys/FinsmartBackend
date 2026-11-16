from typing import Any


def evaluate_condition(cond: dict[str, Any], profile: dict[str, Any]) -> tuple[bool, str]:
    """
    Evaluates a single rule condition against the user demographic profile.
    Returns (is_satisfied, explainable_message).
    """
    field = cond.get("field")
    op = cond.get("op")
    target_val = cond.get("value")
    label = cond.get("label", field)

    if not field or field not in profile or profile[field] is None:
        return False, f"Information needed: {label}"

    user_val = profile[field]

    try:
        if op == "eq":
            ok = user_val == target_val
        elif op == "neq":
            ok = user_val != target_val
        elif op == "gte":
            ok = user_val >= target_val
        elif op == "lte":
            ok = user_val <= target_val
        elif op == "between":
            ok = target_val[0] <= user_val <= target_val[1]
        elif op == "in":
            ok = user_val in target_val
        else:
            ok = False
    except Exception:
        ok = False

    message = f"Criteria satisfied: {label}" if ok else f"Criteria not met: {label}"
    return ok, message


def evaluate_scheme_rules(rule: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluates pure declarative JSON rule dictionary against user demographic profile.
    DSL Structure:
      {"all": [ { "field": "age", "op": "gte", "value": 18, "label": "Age 18+" }, ... ]}
    """
    all_conditions = rule.get("all", [])
    if not all_conditions:
        return {
            "eligible": True,
            "reasons": ["Open to general public without demographic constraints."],
            "matched_conditions": 0,
            "total_conditions": 0
        }

    results = [evaluate_condition(cond, profile) for cond in all_conditions]
    is_eligible = all(res[0] for res in results)
    reasons = [res[1] for res in results]
    matched = sum(1 for res in results if res[0])

    return {
        "eligible": is_eligible,
        "reasons": reasons,
        "matched_conditions": matched,
        "total_conditions": len(all_conditions)
    }

