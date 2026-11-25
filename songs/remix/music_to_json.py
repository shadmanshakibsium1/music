"""
Put this file inside your songs folder and double-click it.

It will create (inside the same folder):
  <FolderName>.json            -> song data
  <FolderName>_covers/         -> cover images (named after each mp3 file)
"""

import json
import subprocess
import sys
import traceback
from pathlib import Path

# Auto-install mutagen if missing
try:
    from mutagen.id3 import ID3, ID3NoHeaderError
except ImportError:
    print("Installing required package (mutagen)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mutagen"])
    from mutagen.id3 import ID3, ID3NoHeaderError


def clean(text):
    return str(text).replace("\ufeff", "").strip()


def get_text(tags, key):
    if tags is None or key not in tags:
        return ""
    values = [clean(v) for v in tags[key].text if clean(v)]
    return ", ".join(values)


def save_cover(tags, dest_dir, stem):
    if tags is None:
        return ""
    pics = tags.getall("APIC")
    if not pics:
        return ""
    pic = next((p for p in pics if p.type == 3), pics[0])
    ext = ".png" if "png" in (pic.mime or "").lower() else ".jpg"
    dest_dir.mkdir(exist_ok=True)
    cover_name = stem + ext
    (dest_dir / cover_name).write_bytes(pic.data)
    return cover_name


def main():
    songs_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    folder_name = songs_dir.name
    covers_dir = songs_dir / f"{folder_name}_covers"
    json_path = songs_dir / f"{folder_name}.json"

    mp3_files = sorted(songs_dir.glob("*.mp3"), key=lambda p: p.name.lower())
    if not mp3_files:
        print("No mp3 files found in:", songs_dir)
        return

    result = []
    for mp3 in mp3_files:
        try:
            tags = ID3(mp3)
        except ID3NoHeaderError:
            tags = None
        except Exception as e:
            print(f"[warning] {mp3.name}: {e}")
            tags = None

        cover = save_cover(tags, covers_dir, mp3.stem)
        result.append({
            "name": get_text(tags, "TIT2") or mp3.stem,
            "artist": get_text(tags, "TPE1"),
            "album": get_text(tags, "TALB"),
            "file": mp3.name,
            "cover": cover,
            "playlist": "",
        })
        print(f"[ok] {mp3.name}" + ("" if cover else "  (no cover)"))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(result)} songs")
    print("JSON  :", json_path)
    print("Covers:", covers_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        input("\nAn error occurred. Press Enter to close...")
