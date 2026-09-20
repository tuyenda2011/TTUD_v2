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
