#!/usr/bin/env python3
"""
Optimize Showing Schedule Script

Zero-context execution script for optimizing property showing schedules.
Uses modified TSP algorithm with priority weighting and availability constraints.

Usage:
    python optimize-showing-schedule.py --properties <ids.json> --date 2026-01-20
    python optimize-showing-schedule.py --properties <ids.json> --date 2026-01-20 --start-time 10:00
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


@dataclass
class ShowingLocation:
    """Property showing location with metadata."""
    property_id: str
    address: str
    coordinates: Tuple[float, float]  # (lat, lng)
    availability_start: str  # HH:MM
    availability_end: str    # HH:MM
    priority: float          # 0-1, higher = show first
    estimated_duration_minutes: int = 30
    match_score: float = 0.0


@dataclass
class ScheduledShowing:
    """A single scheduled showing."""
    sequence: int
    property_id: str
    address: str
    arrival_time: str
    departure_time: str
    showing_duration: int
    drive_time_to: int
    match_score: float
    priority: float


@dataclass
class OptimizedSchedule:
    """Complete optimized schedule result."""
    date: str
    start_time: str
    end_time: str
    total_duration_minutes: int
    total_drive_time_minutes: int
    total_properties: int
    showings: List[ScheduledShowing]
    miles_total: float
    optimization_savings_minutes: int


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance between two coordinates in miles."""
    R = 3959  # Earth's radius in miles

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def estimate_drive_time(distance_miles: float, avg_speed_mph: float = 25) -> int:
    """Estimate drive time in minutes."""
    return max(5, int(distance_miles / avg_speed_mph * 60))


def build_time_matrix(locations: List[Tuple[float, float]]) -> List[List[int]]:
    """Build matrix of drive times between all locations."""
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                distance = haversine_distance(locations[i], locations[j])
                matrix[i][j] = estimate_drive_time(distance)

    return matrix


def build_distance_matrix(locations: List[Tuple[float, float]]) -> List[List[float]]:
    """Build matrix of distances between all locations."""
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine_distance(locations[i], locations[j])

    return matrix


def parse_time(time_str: str) -> datetime:
    """Parse HH:MM time string to datetime."""
    return datetime.strptime(time_str, "%H:%M")


def format_time(dt: datetime) -> str:
    """Format datetime to HH:MM string."""
    return dt.strftime("%H:%M")


def is_within_availability(
    time: datetime,
    availability_start: str,
    availability_end: str
) -> bool:
    """Check if time is within availability window."""
    start = parse_time(availability_start)
    end = parse_time(availability_end)
    time_only = datetime(1900, 1, 1, time.hour, time.minute)

    return start <= time_only <= end


def priority_nearest_neighbor(
    properties: List[ShowingLocation],
    time_matrix: List[List[int]],
    start_time: datetime
) -> List[int]:
    """
    Modified nearest neighbor algorithm with priority weighting.

    Balances distance optimization with showing priorities.
    """
    n = len(properties)
    visited = [False] * n
    route = []
    current_idx = 0  # Start location (index 0 in matrix)
    current_time = start_time

    for _ in range(n):
        best_score = float("inf")
        best_idx = -1

        for i, prop in enumerate(properties):
            if visited[i]:
                continue

            # Calculate drive time from current location
            drive_time = time_matrix[current_idx][i + 1]  # +1 for start offset

            # Check if we can arrive within availability
            arrival = current_time + timedelta(minutes=drive_time)
            if not is_within_availability(
                arrival, prop.availability_start, prop.availability_end
            ):
                continue

            # Score: balance distance and priority
            # Higher priority = lower weight = prefer
            priority_weight = 1.0 - (prop.priority * 0.5)
            weighted_score = drive_time * priority_weight

            if weighted_score < best_score:
                best_score = weighted_score
                best_idx = i

        if best_idx >= 0:
            visited[best_idx] = True
            route.append(best_idx)
            drive_time = time_matrix[current_idx][best_idx + 1]
            current_time += timedelta(
                minutes=drive_time + properties[best_idx].estimated_duration_minutes + 5
            )
            current_idx = best_idx + 1

    return route


def route_total_time(
    route: List[int],
    time_matrix: List[List[int]],
    properties: List[ShowingLocation]
) -> int:
    """Calculate total time for a route including drive and showing time."""
    if not route:
        return 0

    total = 0
    prev_idx = 0  # Start

    for prop_idx in route:
        # Drive time
        total += time_matrix[prev_idx][prop_idx + 1]
        # Showing time
        total += properties[prop_idx].estimated_duration_minutes
        # Buffer
        total += 5
        prev_idx = prop_idx + 1

    return total


def two_opt_improve(
    route: List[int],
    time_matrix: List[List[int]],
    properties: List[ShowingLocation]
) -> List[int]:
    """Improve route using 2-opt swaps."""
    improved = True
    best_route = route.copy()
    best_time = route_total_time(best_route, time_matrix, properties)

    iterations = 0
    max_iterations = 100

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        for i in range(len(best_route) - 1):
            for j in range(i + 2, len(best_route)):
                # Create new route with reversed segment
                new_route = (
                    best_route[:i] +
                    best_route[i:j][::-1] +
                    best_route[j:]
                )

                new_time = route_total_time(new_route, time_matrix, properties)

                if new_time < best_time:
                    best_route = new_route
                    best_time = new_time
                    improved = True

    return best_route


def calculate_naive_time(
    properties: List[ShowingLocation],
    time_matrix: List[List[int]]
) -> int:
    """Calculate time for naive (original order) route."""
    total = 0
    prev_idx = 0

    for i, prop in enumerate(properties):
        total += time_matrix[prev_idx][i + 1]
        total += prop.estimated_duration_minutes + 5
        prev_idx = i + 1

    return total


def build_schedule(
    route: List[int],
    properties: List[ShowingLocation],
    time_matrix: List[List[int]],
    distance_matrix: List[List[float]],
    start_time: str
) -> OptimizedSchedule:
    """Build complete schedule from optimized route."""
    showings = []
    current_time = parse_time(start_time)
    current_idx = 0  # Start location
    total_drive_time = 0
    total_distance = 0.0

    for seq, prop_idx in enumerate(route, 1):
        prop = properties[prop_idx]

        # Calculate drive time and distance
        drive_time = time_matrix[current_idx][prop_idx + 1]
        distance = distance_matrix[current_idx][prop_idx + 1]

        total_drive_time += drive_time
        total_distance += distance

        # Calculate arrival time
        arrival_time = current_time + timedelta(minutes=drive_time)

        # Calculate departure time
        departure_time = arrival_time + timedelta(minutes=prop.estimated_duration_minutes)

        showing = ScheduledShowing(
            sequence=seq,
            property_id=prop.property_id,
            address=prop.address,
            arrival_time=format_time(arrival_time),
            departure_time=format_time(departure_time),
            showing_duration=prop.estimated_duration_minutes,
            drive_time_to=drive_time,
            match_score=prop.match_score,
            priority=prop.priority
        )
        showings.append(showing)

        # Update for next iteration
        current_time = departure_time + timedelta(minutes=5)  # 5 min buffer
        current_idx = prop_idx + 1

    # Calculate totals
    end_time = showings[-1].departure_time if showings else start_time
    start_dt = parse_time(start_time)
    end_dt = parse_time(end_time)
    total_duration = int((end_dt - start_dt).total_seconds() / 60)

    # Calculate naive time for comparison
    naive_time = calculate_naive_time(properties, time_matrix)
    optimization_savings = naive_time - total_duration

    return OptimizedSchedule(
        date="",  # Will be set by caller
        start_time=start_time,
        end_time=end_time,
        total_duration_minutes=total_duration,
        total_drive_time_minutes=total_drive_time,
        total_properties=len(showings),
        showings=showings,
        miles_total=round(total_distance, 1),
        optimization_savings_minutes=max(0, optimization_savings)
    )


def load_properties(properties_file: str) -> List[ShowingLocation]:
    """Load properties from JSON file or generate mock data."""
    try:
        with open(properties_file, 'r') as f:
            data = json.load(f)

        return [
            ShowingLocation(
                property_id=p["property_id"],
                address=p.get("address", "Unknown"),
                coordinates=(p["lat"], p["lng"]),
                availability_start=p.get("availability_start", "09:00"),
                availability_end=p.get("availability_end", "18:00"),
                priority=p.get("priority", 0.5),
                estimated_duration_minutes=p.get("duration", 30),
                match_score=p.get("match_score", 0.0)
            )
            for p in data
        ]
    except FileNotFoundError:
        # Return mock data for demonstration
        return generate_mock_properties()


def generate_mock_properties() -> List[ShowingLocation]:
    """Generate mock properties for demonstration."""
    # Round Rock / Rancho Cucamonga area coordinates
    mock_data = [
        ("prop_001", "123 Main St, Round Rock, TX", (30.508, -97.678), 0.9, 0.85),
        ("prop_002", "456 Oak Ave, Cedar Park, TX", (30.505, -97.820), 0.7, 0.78),
        ("prop_003", "789 Elm Dr, Pflugerville, TX", (30.439, -97.620), 0.8, 0.82),
        ("prop_004", "321 Pine Ln, Georgetown, TX", (30.633, -97.678), 0.6, 0.71),
        ("prop_005", "654 Maple Way, Leander, TX", (30.579, -97.853), 0.5, 0.68),
    ]

    return [
        ShowingLocation(
            property_id=pid,
            address=addr,
            coordinates=coords,
            availability_start="09:00",
            availability_end="18:00",
            priority=priority,
            estimated_duration_minutes=30,
            match_score=score
        )
        for pid, addr, coords, priority, score in mock_data
    ]


def optimize_schedule(
    properties: List[ShowingLocation],
    start_location: Tuple[float, float],
    start_time: str,
    date: str,
    max_duration_hours: float = 4
) -> OptimizedSchedule:
    """
    Main optimization function.

    Combines nearest neighbor heuristic with 2-opt improvement.
    """
    if not properties:
        return OptimizedSchedule(
            date=date,
            start_time=start_time,
            end_time=start_time,
            total_duration_minutes=0,
            total_drive_time_minutes=0,
            total_properties=0,
            showings=[],
            miles_total=0.0,
            optimization_savings_minutes=0
        )

    # Build location list (start + properties)
    all_locations = [start_location] + [p.coordinates for p in properties]

    # Build matrices
    time_matrix = build_time_matrix(all_locations)
    distance_matrix = build_distance_matrix(all_locations)

    # Get initial route using priority-weighted nearest neighbor
    start_dt = parse_time(start_time)
    initial_route = priority_nearest_neighbor(properties, time_matrix, start_dt)

    # Improve route with 2-opt
    optimized_route = two_opt_improve(initial_route, time_matrix, properties)

    # Build schedule
    schedule = build_schedule(
        optimized_route, properties, time_matrix, distance_matrix, start_time
    )
    schedule.date = date

    # Check max duration constraint
    if schedule.total_duration_minutes > max_duration_hours * 60:
        # Remove lowest priority property and retry
        properties_sorted = sorted(properties, key=lambda p: p.priority, reverse=True)
        reduced = properties_sorted[:-1]

        if reduced:
            return optimize_schedule(
                reduced, start_location, start_time, date, max_duration_hours
            )

    return schedule


def main():
    parser = argparse.ArgumentParser(
        description="Optimize property showing schedule"
    )
    parser.add_argument(
        "--properties",
        required=True,
        help="JSON file with property IDs and coordinates, or 'mock' for demo"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Date for showings (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--start-time",
        default="10:00",
        help="Start time (HH:MM, default: 10:00)"
    )
    parser.add_argument(
        "--start-lat",
        type=float,
        default=30.508,
        help="Starting latitude (default: Round Rock)"
    )
    parser.add_argument(
        "--start-lng",
        type=float,
        default=-97.678,
        help="Starting longitude (default: Round Rock)"
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=4,
        help="Maximum duration in hours (default: 4)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Load properties
    if args.properties.lower() == "mock":
        properties = generate_mock_properties()
    else:
        properties = load_properties(args.properties)

    if not properties:
        print("Error: No properties to schedule")
        sys.exit(1)

    # Optimize schedule
    start_location = (args.start_lat, args.start_lng)
    schedule = optimize_schedule(
        properties,
        start_location,
        args.start_time,
        args.date,
        args.max_hours
    )

    # Output results
    if args.output == "json":
        # Convert to dict for JSON serialization
        result = {
            "date": schedule.date,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "total_duration_minutes": schedule.total_duration_minutes,
            "total_drive_time_minutes": schedule.total_drive_time_minutes,
            "total_properties": schedule.total_properties,
            "miles_total": schedule.miles_total,
            "optimization_savings_minutes": schedule.optimization_savings_minutes,
            "showings": [asdict(s) for s in schedule.showings]
        }
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("OPTIMIZED SHOWING SCHEDULE")
        print("=" * 60)
        print(f"\nDate: {schedule.date}")
        print(f"Start Time: {schedule.start_time}")
        print(f"End Time: {schedule.end_time}")
        print(f"Total Duration: {schedule.total_duration_minutes} minutes")
        print(f"Total Drive Time: {schedule.total_drive_time_minutes} minutes")
        print(f"Total Distance: {schedule.miles_total} miles")
        print(f"Time Saved: {schedule.optimization_savings_minutes} minutes")
        print(f"\nProperties: {schedule.total_properties}")

        print("\n" + "-" * 60)
        print("SHOWING SEQUENCE")
        print("-" * 60)

        for showing in schedule.showings:
            print(f"\n{showing.sequence}. {showing.address}")
            print(f"   Property ID: {showing.property_id}")
            print(f"   Arrive: {showing.arrival_time} | Leave: {showing.departure_time}")
            print(f"   Duration: {showing.showing_duration} min | Drive to: {showing.drive_time_to} min")
            print(f"   Match Score: {showing.match_score:.0%} | Priority: {showing.priority:.1f}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
