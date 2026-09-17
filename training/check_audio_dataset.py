import os
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

EXTENSIONS = {".wav", ".WAV"}


def get_audio_info(audio_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries",
        "stream=sample_rate,channels,codec_name,duration",
        "-of", "default=noprint_wrappers=1:nokey=0",
        str(audio_path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "status": "ERROR",
            "error": result.stderr.strip()
        }

    info = {}

    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            info[key] = value

    return {
        "status": "OK",
        "codec": info.get("codec_name"),
        "sample_rate": info.get("sample_rate"),
        "channels": info.get("channels"),
        "duration": info.get("duration")
    }


def main():

    print("=" * 80)
    print("BEE HEALTH DETECTOR - AUDITORÍA DE AUDIOS")
    print("=" * 80)

    files = []

    for class_name in ["healthy", "unhealthy"]:
        class_dir = DATA_DIR / class_name

        if not class_dir.exists():
            print(f"\nADVERTENCIA: no existe {class_dir}")
            continue

        for file in class_dir.iterdir():
            if file.is_file() and file.suffix in EXTENSIONS:
                files.append((class_name, file))

    print(f"\nTotal de audios encontrados: {len(files)}")

    healthy = sum(1 for c, _ in files if c == "healthy")
    unhealthy = sum(1 for c, _ in files if c == "unhealthy")

    print(f"Healthy   : {healthy}")
    print(f"Unhealthy : {unhealthy}")

    print("\n" + "=" * 80)
    print("DETALLE DE LOS AUDIOS")
    print("=" * 80)

    errors = []
    sample_rates = {}
    channels = {}
    durations = []

    for index, (class_name, file) in enumerate(sorted(files), start=1):

        info = get_audio_info(file)

        if info["status"] == "ERROR":
            errors.append(file)

            print(
                f"{index:02d}. "
                f"{class_name.upper():9} | "
                f"{file.name} | "
                f"ERROR"
            )

            continue

        sr = info["sample_rate"]
        ch = info["channels"]
        duration = info["duration"]

        sample_rates[sr] = sample_rates.get(sr, 0) + 1
        channels[ch] = channels.get(ch, 0) + 1

        try:
            duration_float = float(duration)
            durations.append(duration_float)
            duration_text = f"{duration_float:.2f} s"
        except:
            duration_text = "N/A"

        print(
            f"{index:02d}. "
            f"{class_name.upper():9} | "
            f"{file.name:55} | "
            f"SR={sr} | "
            f"CH={ch} | "
            f"DUR={duration_text}"
        )

    print("\n" + "=" * 80)
    print("RESUMEN TÉCNICO")
    print("=" * 80)

    print("\nFrecuencias de muestreo:")
    for sr, count in sorted(sample_rates.items()):
        print(f"  {sr} Hz -> {count} archivos")

    print("\nCanales:")
    for ch, count in sorted(channels.items()):
        print(f"  {ch} canal(es) -> {count} archivos")

    if durations:
        print("\nDuraciones:")
        print(f"  Mínima : {min(durations):.2f} s")
        print(f"  Máxima : {max(durations):.2f} s")
        print(f"  Promedio: {sum(durations) / len(durations):.2f} s")

    print("\nArchivos con errores:")
    print(f"  {len(errors)}")

    if errors:
        for file in errors:
            print(f"  - {file}")

    print("\n" + "=" * 80)
    print("FIN DE LA AUDITORÍA")
    print("=" * 80)


if __name__ == "__main__":
    main()