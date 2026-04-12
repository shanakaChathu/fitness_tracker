import asyncio
import os
from mcp.server.fastmcp import FastMCP
from .whoop_client import whoop_get, whoop_get_paginated, days_ago_iso

mcp = FastMCP(
    "Whoop Fitness Tracker",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8080")),
)


# ── Profile & Body ────────────────────────────────────────────────────────────


@mcp.tool()
async def get_user_profile() -> dict:
    """
    Get the authenticated Whoop user's basic profile information.
    Returns first name, last name, email, and user ID.
    """
    return await whoop_get("/user/profile/basic")


@mcp.tool()
async def get_body_measurements() -> dict:
    """
    Get body measurements on record for the user.
    Returns height (metres), weight (kilograms), and max heart rate (bpm).
    """
    return await whoop_get("/body/measurement")


# ── Recovery ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_latest_recovery() -> dict:
    """
    Get the most recent Whoop recovery score.
    Returns:
      - recovery_score: 0-100 percentage
      - hrv_rmssd_milli: Heart Rate Variability in milliseconds
      - resting_heart_rate: RHR in bpm
      - spo2_percentage: Blood oxygen level
      - skin_temp_celsius: Skin temperature deviation
    """
    records = await whoop_get_paginated("/recovery", {"limit": 1}, max_records=1)
    if not records:
        return {"error": "No recovery data found"}
    return records[0]


@mcp.tool()
async def get_recovery_history(days: int = 7) -> list[dict]:
    """
    Get recovery history for the last N days.

    Args:
        days: Number of days of history to retrieve (1-90, default: 7)

    Returns a list of recovery records sorted newest-first, each containing
    recovery score, HRV, RHR, SpO2, and skin temperature.
    """
    days = max(1, min(days, 90))
    return await whoop_get_paginated(
        "/recovery",
        {"start": days_ago_iso(days), "limit": 25},
        max_records=days,
    )


# ── Sleep ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_latest_sleep() -> dict:
    """
    Get the most recent sleep record.
    Returns:
      - duration_total_in_milli: Total sleep time in milliseconds
      - sleep_performance_percentage: Overall sleep performance score
      - sleep_consistency_percentage: Consistency vs. your sleep schedule
      - sleep_efficiency_percentage: % of time in bed actually asleep
      - stage_summary: Time spent in light, REM, deep sleep, and awake
      - respiratory_rate: Average breaths per minute during sleep
      - is_nap: Whether this was a nap
    """
    records = await whoop_get_paginated("/activity/sleep", {"limit": 1}, max_records=1)
    if not records:
        return {"error": "No sleep data found"}
    return records[0]


@mcp.tool()
async def get_sleep_history(days: int = 7) -> list[dict]:
    """
    Get sleep history for the last N days.

    Args:
        days: Number of days of history to retrieve (1-90, default: 7)

    Returns a list of sleep records including duration, stage breakdowns,
    performance score, and respiratory rate.
    """
    days = max(1, min(days, 90))
    return await whoop_get_paginated(
        "/activity/sleep",
        {"start": days_ago_iso(days), "limit": 25},
        max_records=days,
    )


# ── Workouts ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_recent_workouts(limit: int = 10) -> list[dict]:
    """
    Get the most recent workouts.

    Args:
        limit: Number of workouts to retrieve (1-50, default: 10)

    Returns workouts with sport name, strain score, average/max heart rate,
    kilojoules burned, distance, and time in heart rate zones.
    """
    limit = max(1, min(limit, 50))
    return await whoop_get_paginated(
        "/activity/workout", {"limit": 25}, max_records=limit
    )


@mcp.tool()
async def get_workouts_by_date(start_date: str, end_date: str) -> list[dict]:
    """
    Get all workouts within a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format (e.g. "2024-01-01")
        end_date:   End date in YYYY-MM-DD format (e.g. "2024-01-31")

    Returns all workouts logged between the two dates.
    """
    return await whoop_get_paginated(
        "/activity/workout",
        {
            "start": f"{start_date}T00:00:00.000Z",
            "end": f"{end_date}T23:59:59.999Z",
            "limit": 25,
        },
        max_records=100,
    )


# ── Cycles (Day Strain) ───────────────────────────────────────────────────────


@mcp.tool()
async def get_latest_cycle() -> dict:
    """
    Get the current or most recent physiological cycle (a Whoop 'day').
    Returns day strain score (0-21), kilojoules burned, and average/max heart rate
    for the full day.
    """
    records = await whoop_get_paginated("/cycle", {"limit": 1}, max_records=1)
    if not records:
        return {"error": "No cycle data found"}
    return records[0]


@mcp.tool()
async def get_cycle_history(days: int = 7) -> list[dict]:
    """
    Get physiological cycle (day strain) history for the last N days.

    Args:
        days: Number of days of history to retrieve (1-90, default: 7)

    Returns cycles with strain score, kilojoules, and heart rate data.
    """
    days = max(1, min(days, 90))
    return await whoop_get_paginated(
        "/cycle",
        {"start": days_ago_iso(days), "limit": 25},
        max_records=days,
    )


# ── Summaries ─────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_today_summary() -> dict:
    """
    Get a comprehensive snapshot of today's fitness data in a single call.
    Combines the latest recovery score, most recent sleep, and current day strain.
    Best tool to call when the user asks for a general daily overview.
    """
    recovery, sleep, cycle = await asyncio.gather(
        whoop_get_paginated("/recovery", {"limit": 1}, max_records=1),
        whoop_get_paginated("/activity/sleep", {"limit": 1}, max_records=1),
        whoop_get_paginated("/cycle", {"limit": 1}, max_records=1),
    )
    return {
        "recovery": recovery[0] if recovery else None,
        "sleep": sleep[0] if sleep else None,
        "current_cycle": cycle[0] if cycle else None,
    }


@mcp.tool()
async def get_weekly_summary() -> dict:
    """
    Get a full 7-day summary including recovery, sleep, workouts, and day strain.
    Also returns computed averages for recovery score, HRV, and resting heart rate.
    Use this for trend analysis or weekly check-ins.
    """
    start = days_ago_iso(7)
    params = {"start": start, "limit": 25}

    recovery, sleep, workouts, cycles = await asyncio.gather(
        whoop_get_paginated("/recovery", params, max_records=7),
        whoop_get_paginated("/activity/sleep", params, max_records=7),
        whoop_get_paginated("/activity/workout", params, max_records=20),
        whoop_get_paginated("/cycle", params, max_records=7),
    )

    return {
        "period": "last_7_days",
        "recovery": recovery,
        "sleep": sleep,
        "workouts": workouts,
        "cycles": cycles,
        "averages": {
            "recovery_score": _avg(recovery, "score", "recovery_score"),
            "hrv_rmssd_milli": _avg(recovery, "score", "hrv_rmssd_milli"),
            "resting_heart_rate": _avg(recovery, "score", "resting_heart_rate"),
            "sleep_performance": _avg(sleep, "score", "sleep_performance_percentage"),
            "day_strain": _avg(cycles, "score", "strain"),
        },
    }


@mcp.tool()
async def get_monthly_summary() -> dict:
    """
    Get a 30-day summary of fitness data with computed averages.
    Covers recovery, sleep, workouts, and day strain for the past month.
    """
    start = days_ago_iso(30)
    params = {"start": start, "limit": 25}

    recovery, sleep, workouts, cycles = await asyncio.gather(
        whoop_get_paginated("/recovery", params, max_records=30),
        whoop_get_paginated("/activity/sleep", params, max_records=30),
        whoop_get_paginated("/activity/workout", params, max_records=50),
        whoop_get_paginated("/cycle", params, max_records=30),
    )

    return {
        "period": "last_30_days",
        "total_workouts": len(workouts),
        "recovery": recovery,
        "sleep": sleep,
        "workouts": workouts,
        "cycles": cycles,
        "averages": {
            "recovery_score": _avg(recovery, "score", "recovery_score"),
            "hrv_rmssd_milli": _avg(recovery, "score", "hrv_rmssd_milli"),
            "resting_heart_rate": _avg(recovery, "score", "resting_heart_rate"),
            "sleep_performance": _avg(sleep, "score", "sleep_performance_percentage"),
            "day_strain": _avg(cycles, "score", "strain"),
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _avg(records: list[dict], *keys: str) -> float | None:
    """Extract a nested value from each record and return the average."""
    values: list[float] = []
    for record in records:
        val: Any = record
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                val = None
                break
        if val is not None:
            try:
                values.append(float(val))
            except (TypeError, ValueError):
                pass
    return round(sum(values) / len(values), 2) if values else None


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
