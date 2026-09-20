"""Display declared units and convert time only when the input declares it."""

_TIME_TO_SECONDS = {
    "second": 1.0, "seconds": 1.0, "sec": 1.0, "s": 1.0, "giây": 1.0,
    "minute": 60.0, "minutes": 60.0, "min": 60.0, "phút": 60.0,
    "hour": 3600.0, "hours": 3600.0, "h": 3600.0, "giờ": 3600.0,
}


def unit_label(instance, kind):
    defaults = {"distance": "metre", "time": "minute", "capacity": "capacity_unit"}
    value = instance.metadata.get("units", {}).get(kind, defaults[kind])
    labels = {"metre": "m", "meter": "m", "minute": "phút", "item": "sản phẩm",
              "source_distance_unit": "đơn vị khoảng cách nguồn",
              "source_time_unit": "đơn vị thời gian nguồn",
              "source_size_unit": "đơn vị kích thước nguồn", "capacity_unit": "đơn vị tải"}
    return labels.get(value, value)


def time_scale_seconds(instance):
    """Return seconds per model time unit, or None for an unknown source scale."""
    value = instance.metadata.get("units", {}).get("time", "minute")
    return _TIME_TO_SECONDS.get(str(value).strip().casefold())


def display_snapshot(snapshot):
    """Convert a copy of legacy Kris results using an explicit project convention.

    This is not a verified physical calibration of the author dataset. Keeping
    the raw snapshot untouched preserves benchmark provenance and solver input.
    """
    from copy import deepcopy
    from .models import Instance
    from .solver import fingerprint

    metadata = snapshot['instance'].get('metadata', {})
    units = metadata.get('units', {})
    if (metadata.get('source_kind') != 'author_benchmark'
            or not snapshot['instance']['name'].startswith('Kris-')
            or units.get('distance') != 'source_distance_unit'
            or units.get('time') != 'source_time_unit'):
        return snapshot
    converted = deepcopy(snapshot)
    data = converted['instance']
    distance_factor, time_factor = 0.1, 1 / 1800
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
        'status': 'project_assumption_not_source_verified',
        'metres_per_source_distance': distance_factor,
        'seconds_per_source_time': 1 / 30,
        'scope': 'display_only',
    }
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
