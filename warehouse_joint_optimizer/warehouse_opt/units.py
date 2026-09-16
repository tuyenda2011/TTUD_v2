"""Display declared units without converting values or guessing custom units."""


def unit_label(instance, kind):
    defaults = {"distance": "metre", "time": "minute", "capacity": "capacity_unit"}
    value = instance.metadata.get("units", {}).get(kind, defaults[kind])
    labels = {"metre": "m", "meter": "m", "minute": "phút", "item": "sản phẩm",
              "source_distance_unit": "đv nguồn", "source_time_unit": "đv nguồn",
              "source_size_unit": "đv nguồn", "capacity_unit": "đơn vị tải"}
    return labels.get(value, value)
