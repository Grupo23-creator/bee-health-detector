import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

hives = defaultdict(lambda: {
    "healthy": 0,
    "unhealthy": 0
})


for class_name in ["healthy", "unhealthy"]:

    folder = DATA_DIR / class_name

    for file in folder.iterdir():

        if not file.is_file():
            continue

        match = re.search(r"HIVE?-?(\d+)", file.name, re.IGNORECASE)

        if match:
            hive = match.group(1)
            hives[hive][class_name] += 1


print("=" * 70)
print("DISTRIBUCIÓN DE AUDIOS POR COLMENA")
print("=" * 70)

for hive in sorted(hives, key=int):

    healthy = hives[hive]["healthy"]
    unhealthy = hives[hive]["unhealthy"]
    total = healthy + unhealthy

    print(
        f"HIVE-{hive:>4} | "
        f"Total: {total:2d} | "
        f"Healthy: {healthy:2d} | "
        f"Unhealthy: {unhealthy:2d}"
    )

print("=" * 70)