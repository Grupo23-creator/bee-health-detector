import csv
import re
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = Path(__file__).parent / "audio_manifest.csv"

rows = []

for class_name in ["healthy", "unhealthy"]:

    folder = DATA_DIR / class_name

    for file in sorted(folder.iterdir()):

        if not file.is_file():
            continue

        # Ejemplo:
        # 11-08-2021_16h45_Hive-6.wav
        # 11-08-2021_18h15_HIVE-3693.WAV

        match = re.search(
            r"(\d{2}-\d{2}-\d{4})_(\d{2})h(\d{2})_HIVE?-?(\d+)",
            file.name,
            re.IGNORECASE
        )

        if not match:
            print(f"NO SE PUDO INTERPRETAR: {file.name}")
            continue

        date_str = match.group(1)
        hour = int(match.group(2))
        minute = int(match.group(3))
        hive = match.group(4)

        dt = datetime.strptime(
            f"{date_str} {hour:02d}:{minute:02d}",
            "%d-%m-%Y %H:%M"
        )

        rows.append({
            "filename": file.name,
            "filepath": str(file.relative_to(DATA_DIR.parent.parent)),
            "class": class_name,
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "hive": hive
        })

rows.sort(key=lambda x: x["datetime"])

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "filename",
            "filepath",
            "class",
            "date",
            "time",
            "datetime",
            "hive"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

print("=" * 80)
print("MANIFIESTO DE AUDIOS")
print("=" * 80)

print(f"Total de audios: {len(rows)}")
print(f"Healthy: {sum(r['class'] == 'healthy' for r in rows)}")
print(f"Unhealthy: {sum(r['class'] == 'unhealthy' for r in rows)}")
print(f"Archivo generado: {OUTPUT_FILE}")
print("=" * 80)

print("\nAUDIOS POR FECHA:")
print("-" * 80)

dates = {}

for row in rows:
    dates.setdefault(row["date"], {"healthy": 0, "unhealthy": 0})
    dates[row["date"]][row["class"]] += 1

for date in sorted(dates):
    print(
        f"{date} | "
        f"Healthy: {dates[date]['healthy']:2d} | "
        f"Unhealthy: {dates[date]['unhealthy']:2d}"
    )

print("=" * 80)