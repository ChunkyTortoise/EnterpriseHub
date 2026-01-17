# Showing Optimization Reference

Route optimization and scheduling strategies for property showings.

## Optimization Overview

The showing optimization system creates efficient schedules that minimize drive time while maximizing property viewing effectiveness. It considers travel logistics, property availability, lead preferences, and strategic sequencing.

## Route Optimization Algorithm

### Core TSP Solver

```python
from typing import List, Dict, Tuple
from dataclasses import dataclass
import itertools

@dataclass
class ShowingLocation:
    property_id: str
    address: str
    coordinates: Tuple[float, float]  # (lat, lng)
    availability_windows: List[Tuple[str, str]]  # [(start, end), ...]
    priority: float  # 0-1, higher = show first
    estimated_duration_minutes: int


def optimize_showing_route(
    properties: List[ShowingLocation],
    start_location: Tuple[float, float],
    start_time: str,
    max_duration_hours: float = 4
) -> Dict:
    """
    Optimize showing route using modified TSP algorithm.

    Constraints:
    - Must visit properties within their availability windows
    - Total time <= max_duration_hours
    - Higher priority properties shown earlier
    - Minimize total drive time

    Algorithm:
    1. Build distance/time matrix
    2. Filter by availability
    3. Apply priority-weighted nearest neighbor heuristic
    4. Optimize with 2-opt improvement
    5. Validate against time constraints
    """
    # Build time matrix
    n = len(properties)
    time_matrix = build_time_matrix(
        [start_location] + [p.coordinates for p in properties]
    )

    # Filter available properties
    available = filter_by_availability(properties, start_time, max_duration_hours)

    if not available:
        return {"error": "No properties available in time window"}

    # Initial route using priority-weighted nearest neighbor
    route = priority_nearest_neighbor(
        available, time_matrix, start_location
    )

    # Improve with 2-opt
    optimized_route = two_opt_improve(route, time_matrix)

    # Build schedule with actual times
    schedule = build_schedule(
        optimized_route, time_matrix, start_time, start_location
    )

    # Validate total time
    if schedule["total_duration_minutes"] > max_duration_hours * 60:
        # Remove lowest priority property and re-optimize
        reduced = remove_lowest_priority(available)
        return optimize_showing_route(
            reduced, start_location, start_time, max_duration_hours
        )

    return schedule


def build_time_matrix(locations: List[Tuple[float, float]]) -> List[List[int]]:
    """Build matrix of drive times between all locations."""
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                # Estimate drive time (would use actual API in production)
                distance_miles = haversine_distance(locations[i], locations[j])
                # Assume average 30 mph in suburban areas
                matrix[i][j] = int(distance_miles / 30 * 60)

    return matrix


def priority_nearest_neighbor(
    properties: List[ShowingLocation],
    time_matrix: List[List[int]],
    start: Tuple[float, float]
) -> List[int]:
    """
    Modified nearest neighbor that considers priority.

    Priority influence:
    - High priority (0.8-1.0): Weight distance by 0.5x (prefer priority)
    - Medium priority (0.5-0.7): Weight distance by 0.8x
    - Low priority (0-0.4): Weight distance by 1.0x (pure distance)
    """
    n = len(properties)
    visited = [False] * n
    route = []
    current = 0  # Start location index

    for _ in range(n):
        best_score = float("inf")
        best_idx = -1

        for i, prop in enumerate(properties):
            if visited[i]:
                continue

            # Distance from current location
            distance = time_matrix[current][i + 1]  # +1 for start offset

            # Apply priority weighting
            priority_weight = 1.0 - (prop.priority * 0.5)
            weighted_distance = distance * priority_weight

            if weighted_distance < best_score:
                best_score = weighted_distance
                best_idx = i

        if best_idx >= 0:
            visited[best_idx] = True
            route.append(best_idx)
            current = best_idx + 1

    return route


def two_opt_improve(route: List[int], time_matrix: List[List[int]]) -> List[int]:
    """
    Improve route using 2-opt swaps.

    Keep swapping segments until no improvement found.
    """
    improved = True
    best_route = route.copy()

    while improved:
        improved = False

        for i in range(len(best_route) - 1):
            for j in range(i + 2, len(best_route)):
                # Try reversing segment between i and j
                new_route = (
                    best_route[:i] +
                    best_route[i:j][::-1] +
                    best_route[j:]
                )

                if route_distance(new_route, time_matrix) < route_distance(best_route, time_matrix):
                    best_route = new_route
                    improved = True

    return best_route
```

### Schedule Building

```python
def build_schedule(
    route: List[int],
    time_matrix: List[List[int]],
    start_time: str,
    start_location: Tuple[float, float],
    properties: List[ShowingLocation]
) -> Dict:
    """
    Build detailed schedule with times for each showing.

    Includes:
    - Arrival time at each property
    - Showing duration
    - Buffer time between showings
    - Total drive time
    - Route geometry for map display
    """
    schedule = {
        "start_time": start_time,
        "start_location": start_location,
        "showings": [],
        "total_drive_time_minutes": 0,
        "total_duration_minutes": 0
    }

    current_time = parse_time(start_time)
    current_location_idx = 0  # Start

    for property_idx in route:
        prop = properties[property_idx]

        # Calculate drive time from current location
        drive_time = time_matrix[current_location_idx][property_idx + 1]
        schedule["total_drive_time_minutes"] += drive_time

        # Calculate arrival time
        arrival_time = current_time + timedelta(minutes=drive_time)

        # Check availability window
        if not is_within_availability(arrival_time, prop.availability_windows):
            # Find next available slot
            arrival_time = find_next_available(
                arrival_time, prop.availability_windows
            )

        # Add showing to schedule
        showing = {
            "property_id": prop.property_id,
            "address": prop.address,
            "arrival_time": format_time(arrival_time),
            "showing_duration": prop.estimated_duration_minutes,
            "departure_time": format_time(
                arrival_time + timedelta(minutes=prop.estimated_duration_minutes)
            ),
            "drive_time_to": drive_time,
            "priority": prop.priority
        }
        schedule["showings"].append(showing)

        # Update current position and time
        current_location_idx = property_idx + 1
        current_time = arrival_time + timedelta(
            minutes=prop.estimated_duration_minutes + 5  # 5 min buffer
        )

    # Calculate total duration
    if schedule["showings"]:
        end_time = parse_time(schedule["showings"][-1]["departure_time"])
        start = parse_time(start_time)
        schedule["total_duration_minutes"] = int((end_time - start).total_seconds() / 60)

    return schedule
```

## Strategic Sequencing

### Property Order Strategy

```python
def determine_showing_order(
    properties: List[Dict],
    lead_profile: Dict
) -> List[Dict]:
    """
    Determine strategic order for showings.

    Strategies:
    1. Anchor-first: Start with best match to set expectations
    2. Build-up: Start weaker, end with best (recency effect)
    3. Contrast: Alternate quality to highlight best options
    4. Budget-aware: Show at-budget first, then stretch opportunities
    """
    strategy = select_strategy(lead_profile)

    if strategy == "anchor_first":
        # Best match first to establish baseline
        return sorted(properties, key=lambda p: p["match_score"], reverse=True)

    elif strategy == "build_up":
        # Save best for last (psychological recency)
        return sorted(properties, key=lambda p: p["match_score"])

    elif strategy == "contrast":
        # Alternate high-low-high pattern
        sorted_props = sorted(properties, key=lambda p: p["match_score"], reverse=True)
        result = []
        high_idx, low_idx = 0, len(sorted_props) - 1

        while high_idx <= low_idx:
            if high_idx <= low_idx:
                result.append(sorted_props[high_idx])
                high_idx += 1
            if high_idx <= low_idx:
                result.append(sorted_props[low_idx])
                low_idx -= 1

        return result

    elif strategy == "budget_aware":
        # At-budget first, then stretch opportunities
        at_budget = [p for p in properties if p["within_budget"]]
        stretch = [p for p in properties if not p["within_budget"]]

        return sorted(at_budget, key=lambda p: p["match_score"], reverse=True) + \
               sorted(stretch, key=lambda p: p["match_score"], reverse=True)

    return properties


def select_strategy(lead_profile: Dict) -> str:
    """Select optimal sequencing strategy based on lead profile."""
    # Decision-making stage
    if lead_profile.get("urgency") == "high":
        return "anchor_first"  # Show best immediately

    # Analytical buyers
    if lead_profile.get("decision_style") == "analytical":
        return "build_up"  # Let them compare, end strong

    # Budget-conscious
    if lead_profile.get("budget_sensitivity") == "high":
        return "budget_aware"

    # Emotional/visual buyers
    if lead_profile.get("decision_style") == "emotional":
        return "contrast"  # Create memorable contrasts

    return "anchor_first"  # Default
```

### Timing Optimization

```python
def optimize_timing(
    properties: List[Dict],
    lead_availability: List[Tuple[str, str]],
    property_availability: Dict[str, List[Tuple[str, str]]]
) -> Dict:
    """
    Find optimal day/time for showings.

    Considers:
    - Lead's available times
    - Property showing windows
    - Traffic patterns
    - Best lighting conditions
    - Neighborhood activity levels
    """
    # Find overlapping availability
    viable_windows = find_overlap(lead_availability, property_availability)

    if not viable_windows:
        return {"error": "No common availability found"}

    # Score each window
    scored_windows = []
    for window in viable_windows:
        score = 0.0

        # Weekday vs weekend preference
        if is_weekend(window):
            score += 0.3  # More relaxed viewing

        # Time of day scoring
        hour = get_hour(window)
        if 10 <= hour <= 14:  # Late morning to early afternoon
            score += 0.4  # Best natural lighting
        elif 14 < hour <= 17:
            score += 0.3  # Good time
        elif 17 < hour <= 19:
            score += 0.2  # Evening showing

        # Traffic considerations
        if not is_rush_hour(window):
            score += 0.2

        scored_windows.append({
            "window": window,
            "score": score
        })

    # Return best windows
    return sorted(scored_windows, key=lambda x: x["score"], reverse=True)
```

## Availability Management

### Property Availability Checking

```python
def check_property_availability(
    property_id: str,
    requested_time: str,
    duration_minutes: int = 30
) -> Dict:
    """
    Check if property is available for showing.

    Checks:
    - Listing agent showing hours
    - Existing appointments
    - Lock box / access method
    - Special restrictions (tenant occupied, etc.)
    """
    property_info = get_property_info(property_id)

    # Get showing restrictions
    restrictions = property_info.get("showing_restrictions", {})

    # Check if time is within allowed hours
    showing_hours = restrictions.get("allowed_hours", {"start": "09:00", "end": "20:00"})
    if not is_within_hours(requested_time, showing_hours):
        return {
            "available": False,
            "reason": "Outside showing hours",
            "next_available": find_next_available_time(requested_time, showing_hours)
        }

    # Check existing appointments
    appointments = get_appointments(property_id, get_date(requested_time))
    if has_conflict(requested_time, duration_minutes, appointments):
        return {
            "available": False,
            "reason": "Time slot already booked",
            "alternative_times": find_alternatives(requested_time, appointments)
        }

    # Check special restrictions
    if restrictions.get("tenant_occupied"):
        notice_hours = restrictions.get("notice_required_hours", 24)
        if not has_sufficient_notice(requested_time, notice_hours):
            return {
                "available": False,
                "reason": f"Requires {notice_hours}h notice (tenant occupied)",
                "earliest_available": calculate_earliest(notice_hours)
            }

    return {
        "available": True,
        "access_method": property_info.get("access_method", "lockbox"),
        "access_instructions": property_info.get("access_instructions"),
        "showing_instructions": restrictions.get("special_instructions")
    }
```

### Multi-Property Scheduling

```python
async def schedule_multiple_showings(
    properties: List[str],
    lead_id: str,
    preferred_date: str,
    preferred_time_range: Tuple[str, str]
) -> Dict:
    """
    Schedule multiple showings in one coordinated request.

    Process:
    1. Check all property availability
    2. Optimize route
    3. Create tentative schedule
    4. Confirm with listing agents
    5. Send confirmations
    """
    # Step 1: Check availability in parallel
    availability_tasks = [
        check_property_availability(
            p, preferred_date, preferred_time_range
        )
        for p in properties
    ]
    availability_results = await asyncio.gather(*availability_tasks)

    # Filter to available properties
    available_properties = [
        prop for prop, avail in zip(properties, availability_results)
        if avail["available"]
    ]

    if not available_properties:
        return {
            "success": False,
            "message": "No properties available in requested window",
            "availability_details": availability_results
        }

    # Step 2: Optimize route
    property_details = await get_property_details_batch(available_properties)
    optimized = optimize_showing_route(
        property_details,
        get_lead_location(lead_id),
        preferred_time_range[0]
    )

    # Step 3: Create tentative schedule
    tentative_schedule = create_tentative_appointments(
        optimized, lead_id, preferred_date
    )

    # Step 4: Confirm with listing agents
    confirmation_results = await confirm_appointments_batch(tentative_schedule)

    # Step 5: Build final schedule
    confirmed_showings = [
        s for s, c in zip(tentative_schedule["showings"], confirmation_results)
        if c["confirmed"]
    ]

    return {
        "success": True,
        "confirmed_showings": confirmed_showings,
        "unconfirmed": [
            s for s, c in zip(tentative_schedule["showings"], confirmation_results)
            if not c["confirmed"]
        ],
        "total_drive_time": optimized["total_drive_time_minutes"],
        "route_map_url": generate_route_map(confirmed_showings)
    }
```

## Output Schema

### Schedule Result

```json
{
  "schedule_id": "string",
  "lead_id": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "total_duration_minutes": 0,
  "total_drive_time_minutes": 0,
  "total_properties": 0,

  "showings": [
    {
      "sequence": 1,
      "property_id": "string",
      "address": "string",
      "arrival_time": "HH:MM",
      "departure_time": "HH:MM",
      "showing_duration": 30,
      "drive_time_to": 15,
      "match_score": 0.85,
      "access_method": "lockbox",
      "special_instructions": "string",
      "confirmation_status": "confirmed|pending|unconfirmed"
    }
  ],

  "route": {
    "total_distance_miles": 0.0,
    "waypoints": [
      {
        "lat": 0.0,
        "lng": 0.0,
        "address": "string",
        "type": "start|showing|end"
      }
    ],
    "directions_url": "string"
  },

  "optimization_stats": {
    "time_saved_minutes": 0,
    "miles_saved": 0.0,
    "optimization_method": "priority_nearest_neighbor_2opt"
  }
}
```

## Best Practices

### Scheduling Best Practices

1. **Buffer time** - Add 5-10 minutes between showings for questions
2. **Realistic durations** - Allow 20-30 min for most homes, 45+ for luxury
3. **Traffic awareness** - Avoid scheduling during rush hours
4. **Natural breaks** - Schedule lunch break for 4+ hour tours
5. **Confirmation timing** - Confirm 24-48 hours in advance

### Route Best Practices

1. **Start close** - Begin with properties near lead's current location
2. **Geographic clusters** - Group nearby properties together
3. **Avoid backtracking** - Optimize for efficient loops
4. **End strong** - Save a great property for last
5. **Have alternatives** - Keep backup properties in case of cancellations

### Communication Best Practices

1. **Pre-showing summary** - Send schedule with property highlights
2. **Real-time updates** - Notify of changes immediately
3. **Post-showing follow-up** - Collect feedback same day
4. **Calendar integration** - Sync with lead's calendar
5. **Navigation assistance** - Provide turn-by-turn directions
