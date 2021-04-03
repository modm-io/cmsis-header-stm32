# Script is tested on OS X 10.12
# YOUR MILEAGE MAY VARY

import urllib.request
import zipfile
import shutil
import logging
import os, re, sys
import svn.remote
import subprocess

from pathlib import Path
from multiprocessing.pool import ThreadPool
from socket import timeout

stm32_families = [
    "l0", "l1", "l4", "l5",
    "f0", "f1", "f2", "f3", "f4", "f7",
    "g0", "g4",
    "h7",
    "wb", "wl",
]

def get_header_version(release_notes):
    vmatch = re.search(r">V([0-9]+\.[0-9]+\.[0-9]+)", release_notes)
    return vmatch.group(1) if vmatch else None

def get_header_date(release_notes):
    vmatch = re.search(r">V.+?/.*?(\d{2}-[A-Z][a-z]+?-20\d{2}).*?<", release_notes, flags=re.DOTALL | re.MULTILINE)
    return vmatch.group(1) if vmatch else None

logging.basicConfig(level=logging.DEBUG if "-vv" in sys.argv else logging.INFO)

def get_header_files(family):
    LOGGER = logging.getLogger(family.upper())

    remote_path = Path("raw/STM32{}xx".format(family.upper()))
    repo_url = "https://github.com/STMicroelectronics/STM32Cube{0}/trunk/Drivers/CMSIS/Device/ST/STM32{0}xx".format(family.upper())
    repo = svn.remote.RemoteClient(repo_url)
    repo.export(str(remote_path))

    remote_readme = (remote_path / "Release_Notes.html")
    remote_readme_content = remote_readme.read_text(errors="replace")
    header_remote_version = get_header_version(remote_readme_content)
    header_remote_date = get_header_date(remote_readme_content)

    destination_path = Path("stm32{}xx".format(family))
    header_local_version = (destination_path / "Release_Notes.html")
    if header_local_version.exists():
        header_local_version = get_header_version(header_local_version.read_text(errors="replace"))
    else:
        header_local_version = None
    LOGGER.info("Header v{} -> v{}".format(header_local_version, header_remote_version))

    shutil.rmtree(destination_path, ignore_errors=True)
    destination_path.mkdir(parents=True)
    shutil.copy(remote_readme, destination_path / "Release_Notes.html")
    for path in remote_path.glob("Include/*.h"):
        if not path.is_file(): continue
        dest = destination_path / path.relative_to(remote_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Copy, normalize newline and remove trailing whitespace
        with path.open("r", newline=None, encoding="utf-8", errors="ignore") as rfile, \
                           dest.open("w", encoding="utf-8") as wfile:
            wfile.writelines(l.rstrip()+"\n" for l in rfile.readlines())

    for patch in Path('patches').glob("{}*.patch".format(family)):
        LOGGER.info("Applying {}...".format(patch))
        if os.system("git apply -v --ignore-whitespace {}".format(patch)) != 0:
            LOGGER.critical("Applying {} FAILED...".format(patch))
            return None

    LOGGER.info("Successful update")
    return (header_remote_version, header_remote_date)


shutil.rmtree("raw", ignore_errors=True)
Path("raw").mkdir()
with ThreadPool(len(stm32_families)) as pool:
    family_versions = pool.map(get_header_files, stm32_families)


def update_readme(readme, family, new_version, new_date):
    match = r"{0}: v.+? created .+?]".format(family.upper())
    replace = "{0}: v{1} created {2}]".format(family.upper(), new_version, new_date)
    return re.sub(match, replace, readme)

for family, versions in zip(stm32_families, family_versions):
    if versions is None or versions[0] is None: continue;
    readme = Path("README.md").read_text()
    readme = update_readme(readme, family, versions[0], versions[1])
    Path("README.md").write_text(readme)
    subprocess.run("git add README.md stm32{}xx".format(family), shell=True)
    if subprocess.call("git diff-index --quiet HEAD --", shell=True):
        subprocess.run('git commit -m "Update STM32{} headers to v{}"'.format(family.upper(), versions[0]), shell=True)

exit(family_versions.count(None))
