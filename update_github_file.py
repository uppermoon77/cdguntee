import os
import re
import time
import requests
from github import Github, GithubException

# --- KONFIGURASI ---
GITHUB_TOKEN = os.getenv('GITHUB_PAT')  # Ambil dari environment variable
# Gunakan pola raw yang valid: https://raw.githubusercontent.com/<user>/<repo>/<branch>/<path>
SOURCE_URL   = "https://raw.githubusercontent.com/uppermoon77/cdguntee/main/cdguntee"
DEST_REPO    = "uppermoon77/cdguntee"  # Format: "username/repository" 
GIT_BRANCH   = "main"
COMMIT_MSG   = "Auto update: Sync playlist from source + footer update"
SLEEP_BETWEEN_COMMITS_SEC = 0.7         # jeda antar commit

# --- FOOTER TOOLS ---
FOOTER_REGEX = r'#EXTM3U billed-msg="[^"]+"'

def generate_footer(dest_file_path: str) -> str:
    return f'#EXTM3U billed-msg="😎{dest_file_path}| lynk.id/magelife😎"'

def strip_footer(text: str) -> str:
    return re.sub(FOOTER_REGEX, '', text).strip()

def add_footer(text: str, dest_file_path: str) -> str:
    cleaned = strip_footer(text)
    return f"{cleaned}\n\n{generate_footer(dest_file_path)}\n"

# --- AMBIL KONTEN DARI SOURCE ---
def get_source_content() -> str | None:
    try:
        print(f"Mengambil konten dari: {SOURCE_URL} ...")
        headers = {"User-Agent": "MagelifeSync/1.0 (+https://lynk.id/magelife)"}
        r = requests.get(SOURCE_URL, timeout=30, headers=headers)
        r.raise_for_status()
        print("✅ Konten berhasil diambil.")
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil konten sumber: {e}")
        return None

# --- UPDATE FILE SATU PER SATU ---
def update_single_file(g: Github, dest_file_path: str, base_content_no_footer: str) -> None:
    new_content_with_footer = add_footer(base_content_no_footer, dest_file_path)
    repo = g.get_repo(DEST_REPO)

    print(f"\n🟦 Memproses file: {dest_file_path}")

    try:
        contents = repo.get_contents(dest_file_path, ref=GIT_BRANCH)
        sha = contents.sha
        old_text = contents.decoded_content.decode("utf-8")
        old_no_footer = strip_footer(old_text)

        # Cek apakah konten sama (tanpa footer)
        if old_no_footer.strip() == base_content_no_footer.strip():
            print("➡️  Tidak ada perubahan, skip.")
            return

        # Update file jika ada perubahan
        print("✏️  Ada perubahan, memperbarui file...")
        repo.update_file(
            path=contents.path,
            message=COMMIT_MSG,
            content=new_content_with_footer,
            sha=sha,
            branch=GIT_BRANCH
        )
        print("✅ File berhasil di-update!")

    except GithubException as e:
        if getattr(e, "status", None) == 404:
            print("🆕 File belum ada, membuat baru...")
            repo.create_file(
                path=dest_file_path,
                message=COMMIT_MSG,
                content=new_content_with_footer,
                branch=GIT_BRANCH
            )
            print("✅ File baru berhasil dibuat.")
        else:
            print(f"❌ Error API GitHub: {e}")
    except Exception as e:
        print(f"❌ Error tak terduga: {e}")

# --- GENERATE FILE NAME OTOMATIS UNTUK NOVEMBER 2025 ---
def generate_november_files() -> list[str]:
    month = "NOVEMBER"
    year = "2025"
    prefix = "CD"
    # 1 s/d 30, dengan zero-pad agar rapi: CD01NOVEMBER2025 ... CD30NOVEMBER2025
    return [f"{prefix}{day:02d}{month}{year}" for day in range(1, 31)]

# --- MAIN ---
def main():
    if not GITHUB_TOKEN:
        print("❌ Error: environment variable GITHUB_PAT belum diatur.")
        return

    # Ambil konten dari source
    src = get_source_content()
    if not src:
        return

    base_no_footer = strip_footer(src)
    g = Github(GITHUB_TOKEN)

    # Daftar file target (1-30 November)
    target_files = generate_november_files()
    print(f"\n📁 Daftar file target ({len(target_files)}):")
    print(target_files)

    for idx, dest_file_path in enumerate(target_files, start=1):
        print(f"\n({idx}/{len(target_files)}) Mulai update {dest_file_path}...")
        update_single_file(g, dest_file_path, base_no_footer)
        time.sleep(SLEEP_BETWEEN_COMMITS_SEC)

    print("\n🎯 Semua file selesai diproses!")

if __name__ == "__main__":
    main()
