"""Read the authors' corrected Kris format without inventing orders or due dates."""
import hashlib
from pathlib import Path

from .models import Edge, InputError, Instance, Node, Operations, Order, Product

SOURCE = "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/index.html"
FORMAT = "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/data/format.txt"
SCALARS = {"alpha", "NbLocations", "NbProducts", "NbPickers", "CapaPicker", "TimeToTravelOneDistanceUnit", "SetupTime", "PickTime", "NbOrders", "NbVerticesIntersections", "DepartingDepot", "ArrivalDepot"}


def read_kris(path):
    """Preserve native units; verified coincident source/sink copies are contracted.

    This is a DATA adapter to the project's soft-due-date objective, not a
    reproduction of the authors' hard-deadline optimization problem.
    """
    path = Path(path)
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    sections, current = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("//"):
            heading = line[2:].strip()
            if heading in SCALARS:
                current = heading
            elif heading.startswith("Idx Location Size"):
                current = "product_rows"
            elif heading.startswith("Idx DueDate TardinessPenalty"):
                current = "order_rows"
            elif heading == "Start End Distance":
                current = "arcs"
            elif heading.startswith("LocStart LocEnd ShortestPath"):
                current = "distances"
            elif heading == "Loc x y":
                current = "coordinates"
            else:
                current = None
            if current:
                if current in sections:
                    raise InputError(f"Duplicate Kris section: {current}")
                sections[current] = []
        elif current:
            sections[current].append(line)
        else:
            raise InputError(f"Unrecognized Kris data section near: {line[:80]}")
    try:
        def scalar(key):
            rows = sections[key]
            if len(rows) != 1:
                raise InputError(f"Expected one value for {key}")
            return float(rows[0])

        def integer(key):
            value = scalar(key)
            if not value.is_integer():
                raise InputError(f"Non-integer {key}")
            return int(value)

        start, finish = str(integer("DepartingDepot")), str(integer("ArrivalDepot"))
        coords = {}
        for line in sections["coordinates"]:
            node, x, y, *_ = line.split(maxsplit=3)
            if node in coords:
                raise InputError("Duplicate node coordinate")
            coords[node] = (float(x), float(y))
        arcs = {}
        for line in sections["arcs"]:
            u, v, length = line.split()
            if (u, v) in arcs:
                raise InputError("Duplicate directed arc in source")
            arcs[u, v] = float(length)
        if start != finish:
            if coords[start] != coords[finish]:
                raise InputError("Distinct physical depots cannot be contracted")
            outgoing = {v: d for (u, v), d in arcs.items() if u == start}
            incoming = {u: d for (u, v), d in arcs.items() if v == finish}
            if len(outgoing) != 1 or outgoing != incoming:
                raise InputError("Source/sink depot copies do not have matching aisle connections")
            if any(v == start or u == finish for u, v in arcs):
                raise InputError("Unexpected arcs into source or out of sink depot")
        def canonical(node):
            return start if node == finish else node
        mapped = {}
        for (u, v), distance in arcs.items():
            pair = canonical(u), canonical(v)
            if pair[0] == pair[1]:
                raise InputError("Contracting depots would create a self-loop")
            if pair in mapped and mapped[pair] != distance:
                raise InputError("Conflicting depot edge lengths")
            mapped[pair] = distance
        if any(mapped.get((v, u)) != length for (u, v), length in mapped.items()):
            raise InputError("Source graph remains directed/asymmetric; not compatible with current router")
        edges = [Edge(u, v, d) for (u, v), d in sorted(mapped.items()) if u < v]
        nodes = [Node(node, *xy) for node, xy in coords.items() if node != finish or start == finish]
        products = []
        for row in sections["product_rows"]:
            sku, location, size = row.split()
            products.append(Product(sku, canonical(location), float(size), scalar("PickTime")))
        if len(products) != integer("NbProducts"):
            raise InputError("Product count does not match source header")
        orders, penalties = [], {}
        for rank, row in enumerate(sections["order_rows"]):
            values = row.split()
            oid, due, penalty, count = values[:4]
            if len(values) != 4 + 2 * int(count):
                raise InputError(f"Malformed item list in order {oid}")
            items = {}
            for sku, qty in zip(values[4::2], values[5::2]):
                quantity = int(qty)
                if quantity <= 0:
                    raise InputError(f"Nonpositive quantity in order {oid}")
                items[sku] = items.get(sku, 0) + quantity
            orders.append(Order(oid, items, float(due), rank))
            penalties[oid] = float(penalty)
        if len(orders) != integer("NbOrders"):
            raise InputError("Order count does not match source header")
        travel_time = scalar("TimeToTravelOneDistanceUnit")
        if travel_time <= 0:
            raise InputError("TimeToTravelOneDistanceUnit must be positive")
        instance = Instance(f"Kris-{path.stem}", start, nodes, edges, products, orders,
            Operations(pickers=integer("NbPickers"), capacity=scalar("CapaPicker"), speed=1 / travel_time,
                       location_minutes=0., batch_minutes=scalar("SetupTime")),
            {"source": SOURCE, "format_source": FORMAT, "source_file": path.name,
             "source_sha256": hashlib.sha256(raw).hexdigest(), "source_kind": "author_benchmark", "generated_by_this_project": False,
             "units": {"distance": "source_distance_unit", "time": "source_time_unit", "capacity": "source_size_unit"},
             "due_dates": {"regenerated": False, "rule": "unchanged source DueDate column"},
             "source_parameters": {key: scalar(key) for key in SCALARS},
             "source_tardiness_penalties": penalties,
             "conversion": {"depot_copies": [start, finish], "depot_contraction_verified": start != finish,
                 "units_rescaled": False, "pick_time_interpretation": "per item quantity",
                 "location_service_added": 0,
                 "target_objective": "project normalized distance/makespan/soft tardiness; source alpha and penalties retained as metadata, not used as objective weights",
                 "source_problem": "JOBPRSP-D / hard deadlines; source best-known objectives are not directly comparable"}})
        return instance.validate()
    except (KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError(f"Invalid or unsupported Kris file {path.name}: {exc}") from exc
