"""Sanitized Kumu relationship export from local evidence."""
import csv
from pathlib import Path


def export(records, directory):
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    elements, connections = {}, set()
    def element(identifier, label, kind):
        elements[identifier] = (identifier, label, kind)
    for record in records:
        case = str(record["case_id"])
        track = str(record["track"])
        model = str(record.get("model") or "unspecified")
        boundary = str(record.get("boundary") or "unknown")
        run = str(record["run_id"])
        element("case:" + case, case, "Test case")
        element("track:" + track, track, "Track")
        element("model:" + model, model, "Model")
        element("boundary:" + boundary, boundary, "Trust boundary")
        element("run:" + run, run, "Experiment")
        connections.update({("case:" + case, "boundary:" + boundary, "targets"),
                            ("run:" + run, "case:" + case, "tests"),
                            ("run:" + run, "track:" + track, "uses"),
                            ("run:" + run, "model:" + model, "uses")})
    with (destination / "elements.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("id", "label", "type"))
        writer.writerows(sorted(elements.values()))
    with (destination / "connections.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("from", "to", "label"))
        writer.writerows(sorted(connections))
    return len(elements), len(connections)
