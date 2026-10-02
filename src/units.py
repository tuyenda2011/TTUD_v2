"""Display declared units and apply explicit demo conventions to a copy."""
from copy import deepcopy
import math

from .models import InputError

# Project demo convention, not a physical calibration of the author benchmark.
KRIS_DISPLAY_CONVENTION = {
    "metres_per_source_distance": 0.1,
    "seconds_per_source_time": 1 / 30,
}

_TIME_TO_SECONDS = {
    "second": 1.0, "seconds": 1.0, "sec": 1.0, "s": 1.0, "giây": 1.0,
    "minute": 60.0, "minutes": 60.0, "min": 60.0, "phút": 60.0,
    "hour": 3600.0, "hours": 3600.0, "hr": 3600.0, "hrs": 3600.0, "h": 3600.0, "giờ": 3600.0,
}

_UNIT_LABELS = {
    "metre": "m", "metres": "m", "meter": "m", "meters": "m", "m": "m", "mét": "m",
    "item": "sản phẩm", "items": "sản phẩm", "sản phẩm": "sản phẩm",
    "source_distance_unit": "đơn vị khoảng cách nguồn",
    "source_time_unit": "đơn vị thời gian nguồn",
    "source_size_unit": "đơn vị kích thước nguồn", "capacity_unit": "đơn vị tải",
    **{name: {1.0: "giây", 60.0: "phút", 3600.0: "giờ"}[scale] for name, scale in _TIME_TO_SECONDS.items()},
}


def unit_label(instance, kind):
    defaults = {"distance": "metre", "time": "minute", "capacity": "capacity_unit"}
    value = instance.metadata.get("units", {}).get(kind, defaults[kind]).strip()
    return _UNIT_LABELS.get(value.casefold(), value)


def time_scale_seconds(instance):
    """Return seconds per model time unit, or None when its scale is unknown."""
    value = instance.metadata.get("units", {}).get("time", "minute")
    return _TIME_TO_SECONDS.get(str(value).strip().casefold())


def format_duration(value, instance):
    """Format known time scales with JS-compatible half-up rounding to seconds."""
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value)):
        raise InputError("Duration must be a finite number")
    value = max(0, value)
    scale = time_scale_seconds(instance)
    if scale is None:
        return f"{value:.12g} {unit_label(instance, 'time')}"
    seconds = value * scale
    if not math.isfinite(seconds):
        raise InputError("Duration exceeds the supported clock range")
    total = math.floor(seconds + .5)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours} giờ {minutes:02d} phút {seconds:02d} giây"
    return f"{minutes} phút {seconds:02d} giây"


def display_snapshot(snapshot, convention=None):
    """Convert only Kris views with an explicit convention; keep exports native."""
    metadata = snapshot['instance'].get('metadata', {})
    units = metadata.get('units', {})
    if (convention is None or metadata.get('source_kind') != 'author_benchmark'
            or not snapshot['instance']['name'].startswith('Kris-')
            or units.get('distance') != 'source_distance_unit'
            or units.get('time') != 'source_time_unit'):
        return snapshot
    for key in ('metres_per_source_distance', 'seconds_per_source_time'):
        value = convention.get(key)
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(value) or value <= 0):
            raise InputError(f'{key} must be a positive finite number')
    distance_factor = convention['metres_per_source_distance']
    time_factor = convention['seconds_per_source_time'] / 60
    converted = deepcopy(snapshot)
    data = converted['instance']
    for node in data['nodes']:
        node['x'] *= distance_factor
        node['y'] *= distance_factor
    for edge in data['edges']:
        edge['distance'] *= distance_factor
    for product in data['products']:
        product['pick_minutes'] *= time_factor
    for order in data['orders']:
        order['due'] *= time_factor
    op = data['operations']
    op['speed'] *= distance_factor / time_factor
    for key in ('location_minutes', 'batch_minutes'):
        op[key] *= time_factor
    data['metadata']['units'].update(distance='metre', time='minute')
    data['metadata']['display_conversion'] = {
        **convention, 'status': 'project_demo_convention', 'scope': 'display_only',
    }
    from .models import Instance
    from .solver import fingerprint

    instance_hash = fingerprint(Instance.from_dict(data))
    for result in converted['results'].values():
        result['instance_sha256'] = instance_hash
        result['picker_ends'] = [value * time_factor for value in result['picker_ends']]
        result['metrics']['distance'] *= distance_factor
        for key in ('makespan', 'tardiness'):
            result['metrics'][key] *= time_factor
        refs = result['objective_config']
        refs['distance_ref'] *= distance_factor
        for key in ('completion_ref', 'tardiness_ref'):
            refs[key] *= time_factor
        for batch in result['batches']:
            batch['distance'] *= distance_factor
            for key in ('start', 'end', 'duration', 'tardiness'):
                batch[key] *= time_factor
        for order in result['orders']:
            for key in ('due', 'completion', 'tardiness'):
                order[key] *= time_factor
    return converted
