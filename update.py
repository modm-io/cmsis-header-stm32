# Script is tested on OS X 10.12
# YOUR MILEAGE MAY VARY

import urllib.request
import zipfile
import shutil
import sys
import re
import os
from pathlib import Path

stm32_families = [
    "l0", "l1", "l4",
    "f0", "f1", "f2", "f3", "f4", "f7",
    "h7"
]

def get_local_cube_version(readme, family):
    regex = r"Cube{} v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)\)".format(family.upper())
    match = re.search(regex, readme)
    return match.group("version") if match else None

def get_header_version(release_notes):
    vmatch = re.search(r">V([0-9]+\.[0-9]+\.[0-9]+)", release_notes)
    return vmatch.group(1) if vmatch else None

def get_header_date(release_notes):
    vmatch = re.search(r">V.+?/.*?(\d{2}-[A-Z][a-z]+?-20\d{2}).*?<", release_notes, flags=re.DOTALL | re.MULTILINE)
    return vmatch.group(1) if vmatch else None

def get_remote_cube_version(html):
    vmatch = re.search(r"    (?P<version>[0-9]+\.[0-9]+\.[0-9]+)", html)
    return vmatch.group("version") if vmatch else None

def get_remote_zip_url(html, family):
    dlmatch = re.search(r"data-download-path=\"(?P<dlurl>/content/ccc/resource/.*?cube{}\.zip)\"".format(family), html)
    return "https://www.st.com" + dlmatch.group("dlurl") if dlmatch else None

def remote_is_newer(local, remote):
    if "x" in local or "x" in remote:
        print("Unknown version format")
        return False
    for l, r in zip(local.split('.'), remote.split('.')):
        if int(l) < int(r):
            return True
    return False

download_remote = ("-d" in sys.argv)
force_update = ("-f" in sys.argv)

cube_local_version = {}
header_local_version = {}
# parse the versions directly from the README
readme = Path("README.md").read_text()
for family in stm32_families:
    # extract local cube version from local readme
    cube_local_version[family] = get_local_cube_version(readme, family)
    if not cube_local_version[family]:
        print("No version match in local Readme for", family)
        exit(1)
    # extract local header version from local release notes
    with open("stm32{}xx/Release_Notes.html".format(family), "r", errors="replace") as html:
        header_local_version[family] = get_header_version(html.read())
    if not header_local_version[family]:
        print("No version match in local release notes for", family)
        exit(1)

cube_remote_version = {}
cube_dl_url = {}
cube_furl = "http://www.st.com/en/embedded-software/stm32cube{}.html"
# parse the versions and download links from ST's website
for family in stm32_families:
    with urllib.request.urlopen(cube_furl.format(family)) as response:
        html = response.read().decode("utf-8")
        # extract remote cube version from website
        cube_remote_version[family] = get_remote_cube_version(html)
        if not cube_remote_version[family]:
            print("No version match in remote html for", family)
            exit(1)
        # extract cube download link from website
        cube_dl_url[family] = get_remote_zip_url(html, family)
        if not cube_dl_url[family]:
            print("No zip download link for", family)
            exit(1)

# compare all versions and print a status page
check_header_version = [f for f in stm32_families if remote_is_newer(cube_local_version[f], cube_remote_version[f])]
if force_update: check_header_version = stm32_families;

# intermediate report on cube versions
for family in stm32_families:
    status = "{}: Cube   v{} -> v{}\t{}"
    print(status.format(family.upper(), cube_local_version[family], cube_remote_version[family],
            "update!" if family in check_header_version else "ok"))

header_remote_version = {}
header_remote_date = {}
# compare local and remote header versions
for family in check_header_version:
    # download cmsis pack into zip file
    dl_count = 0
    if download_remote:
        print("Downloading '{}.zip' ...\n{}".format(family, cube_dl_url[family]))
    while(1):
        dl_file = "{}.zip".format(family)
        if download_remote:
            with urllib.request.urlopen(cube_dl_url[family]) as response, \
                                  open(dl_file, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
            dl_count += 1
        print("Extracting '{}.zip' ...".format(family))
        # extract the remote header version from the zip file
        try:
            with zipfile.ZipFile(dl_file, "r") as zip_ref:
                base_name = zip_ref.namelist()[0].split("/")[0]
                release_note_path = "{}/Drivers/CMSIS/Device/ST/STM32{}xx/Release_Notes.html".format(base_name, family.upper())
                # only read the release notes, we don't care about the rest
                html = zip_ref.read(release_note_path).decode("utf-8", errors="replace")
                header_remote_version[family] = get_header_version(html)
                header_remote_date[family] = get_header_date(html)
            break
        except:
            if (dl_count > 10):
                print("===>>> Bad zipfile for {}! <<<===".format(family))
                header_remote_version[family] = "x.x.x"
                break
            else:
                print("<<<=== Retrying zipfile for {}! ===>>>".format(family))
    if not header_remote_version[family]:
        print("No version match in remote release notes for", family)
        exit(1)

print()
headers_updated = []
for family in check_header_version:
    status = "{}: Header v{} -> v{}\t{}"
    hl = header_local_version[family]
    hr = header_remote_version[family]
    print(status.format(family.upper(), hl, hr, "update!" if remote_is_newer(hl, hr) else "ok"))
    try:
        print("Replacing headers stm32{}xx...".format(family))
        with zipfile.ZipFile("{}.zip".format(family), "r") as zip_ref:
            base_name = "{}/Drivers/CMSIS/Device/ST/STM32{}xx/".format(zip_ref.namelist()[0].split("/")[0], family.upper())
            destination_path = "stm32{}xx".format(family)
            sources = ["Release_Notes.html", "Include/s"]
            for member in zip_ref.namelist():
                if any(member.startswith(os.path.join(base_name, src)) for src in sources):
                    with zip_ref.open(member) as mem, \
                        open(os.path.join(destination_path, member.replace(base_name, '')), "wb") as dp:
                        shutil.copyfileobj(mem, dp)
        headers_updated.append(family)
    except zipfile.BadZipFile:
        print("Skipping bad zip file for stm32{}xx...".format(family))
        pass

print("Normalizing newlines and whitespace...", flush=True)
if os.system("sh ./post_script.sh > /dev/null 2>&1") != 0:
    print("Normalizing newlines and whitespace FAILED...")
    exit(1)

for family in headers_updated:
    for patch in Path('patches').glob("{}*.patch".format(family)):
        print("Applying {}...".format(patch))
        if os.system("git apply -v --ignore-whitespace {}".format(patch)) != 0:
            print("Applying {} FAILED...".format(patch))
            exit(1)

def update_readme(readme, family, new_version, new_date, new_cube):
    match = r"{0}: v.+? created .+? \(Cube{0} v.+?\)".format(family.upper())
    replace = "{0}: v{1} created {2} (Cube{0} v{3})".format(
                    family.upper(), new_version, new_date, new_cube)
    return re.sub(match, replace, readme)

for family in headers_updated:
    readme = update_readme(readme, family,
                           header_remote_version[family],
                           header_remote_date[family],
                           cube_remote_version[family])
Path("README.md").write_text(readme)
