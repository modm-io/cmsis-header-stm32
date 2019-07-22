# Script is tested on OS X 10.12
# YOUR MILEAGE MAY VARY

import urllib.request
import zipfile
import shutil
import logging
import os, re, sys

from pathlib import Path
from multiprocessing.pool import ThreadPool
from socket import timeout

# Set the right headers
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

stm32_families = [
    "l0", "l1", "l4",
    "f0", "f1", "f2", "f3", "f4", "f7",
    "g0", "g4",
    "h7",
    "wb"
]
readme = Path("README.md").read_text()

def get_local_cube_version(family):
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
    dlmatch = re.search(r"data-download-path=\"(?P<dlurl>/content/ccc/resource/.*?stm32cube{}\.zip)\"".format(family), html)
    return "https://www.st.com" + dlmatch.group("dlurl") if dlmatch else None

def remote_is_newer(local, remote):
    if "x" in local or "x" in remote:
        print("Unknown version format")
        return False
    for l, r in zip(local.split('.'), remote.split('.')):
        if int(l) < int(r):
            return True
    return False


download_remote = "-d" in sys.argv
force_update = "-f" in sys.argv
logging.basicConfig(level=logging.DEBUG if "-vv" in sys.argv else logging.INFO)

def get_header_files(family):
    LOGGER = logging.getLogger(family.upper())
    cube_furl = "http://www.st.com/en/embedded-software/stm32cube{}.html"
    header_local_version = None
    LOGGER.debug("Parsing local header versions...")
    # parse the versions directly from the README
    # extract local cube version from local readme
    cube_local_version = get_local_cube_version(family)
    if cube_local_version is None:
        LOGGER.critical("No version match in local Readme")
        return None
    # extract local header version from local release notes
    header_local_version = get_header_version(Path("stm32{}xx/Release_Notes.html".format(family)).read_text(errors="replace"))
    if header_local_version is None:
        LOGGER.critical("No version match in local release notes")
        return None

    cube_remote_version = None
    cube_dl_url = None
    # parse the versions and download links from ST's website
    LOGGER.debug("Downloading homepage...")
    dl_count = 10
    while(dl_count >= 0):
        try:
            with urllib.request.urlopen(urllib.request.Request(cube_furl.format(family), headers=hdr), timeout=30) as response:
                size = response.getheader('Content-Length')
                if size is not None:
                    LOGGER.debug("Homepage size: {:0.0f} kB".format(int(size)/1e3))
                html = response.read().decode("utf-8")
                # extract remote cube version from website
                cube_remote_version = get_remote_cube_version(html)
                if cube_remote_version is None:
                    LOGGER.critical("No version match in remote html")
                    return None
                # extract cube download link from website
                cube_dl_url = get_remote_zip_url(html, family)
                if cube_dl_url is None:
                    LOGGER.critical("No zip download link")
                    return None
                break
        except timeout:
            dl_count -= 1
            if (dl_count <= 0):
                LOGGER.critical("Failed to download homepage")
                return None

    # compare all versions and print a status page
    check_header_version = force_update or remote_is_newer(cube_local_version, cube_remote_version)

    # intermediate report on cube versions
    LOGGER.info("Cube   v{:7} -> v{:7}   {}".format(cube_local_version, cube_remote_version,
                                               "update!" if check_header_version else "ok"))
    # Return False = "no changes"
    if not check_header_version:
        return (cube_remote_version, None, None)

    header_remote_version = None
    header_remote_date = None
    dl_file = "{}.zip".format(family)
    # download cmsis pack into zip file
    if download_remote:
        LOGGER.debug("Downloading {}".format(cube_dl_url))
        dl_count = 10
        while(dl_count >= 0):
            try:
                with urllib.request.urlopen(urllib.request.Request(cube_dl_url, headers=hdr), timeout=300) as response, \
                     open(dl_file, "wb") as out_file:
                    size = response.getheader('Content-Length')
                    if size is not None:
                        LOGGER.debug("Zipfile size: {:0.1f} MB".format(int(size)/1e6))
                    shutil.copyfileobj(response, out_file)
                break
            except timeout:
                dl_count -= 1
                if (dl_count <= 0):
                    LOGGER.critical("Failed to download zipfile")
                    return None

    LOGGER.debug("Extracting zipfile...")
    dl_count = 10
    while(dl_count >= 0):
        # extract the remote header version from the zip file
        try:
            with zipfile.ZipFile(dl_file, "r") as zip_ref:
                base_name = zip_ref.namelist()[0].split("/")[0]
                release_note_path = "{}/Drivers/CMSIS/Device/ST/STM32{}xx/Release_Notes.html".format(base_name, family.upper())
                # only read the release notes, we don't care about the rest
                html = zip_ref.read(release_note_path).decode("utf-8", errors="replace")
                header_remote_version = get_header_version(html)
                header_remote_date = get_header_date(html)
            break
        except:
            if (dl_count <= 0):
                LOGGER.critical("===>>> Bad zipfile! <<<===")
                return None
            else:
                LOGGER.error("<<<=== Retrying zipfile! ===>>>")
            dl_count -= 1
    if header_remote_version is None:
        LOGGER.critical("No version match in remote release notes")
        return None

    headers_updated = False
    LOGGER.info("Header v{:7} -> v{:7}   {}".format(header_local_version, header_remote_version,
                "update!" if remote_is_newer(header_local_version, header_remote_version) else "ok"))
    try:
        LOGGER.info("Replacing headers...")
        destination_path = "stm32{}xx".format(family)
        for fobj in Path(destination_path).glob("Include/*"):
            fobj.unlink()
        with zipfile.ZipFile("{}.zip".format(family), "r") as zip_ref:
            base_name = "{}/Drivers/CMSIS/Device/ST/STM32{}xx/".format(
                        zip_ref.namelist()[0].split("/")[0], family.upper())
            sources = ["Release_Notes.html", "Include/s"]
            for member in zip_ref.namelist():
                if any(member.startswith(os.path.join(base_name, src)) for src in sources):
                    with zip_ref.open(member) as mem, \
                         open(os.path.join(destination_path, member.replace(base_name, '')), "wb") as dp:
                        shutil.copyfileobj(mem, dp)
        headers_updated = True
    except zipfile.BadZipFile:
        LOGGER.error("Skipping bad zip file...")
        pass

    LOGGER.debug("Normalizing newlines and whitespace...")
    if os.system("sh ./post_script.sh stm32{}xx > /dev/null 2>&1".format(family)) != 0:
        LOGGER.critical("Normalizing newlines and whitespace FAILED...")
        return None

    for patch in Path('patches').glob("{}*.patch".format(family)):
        LOGGER.info("Applying {}...".format(patch))
        if os.system("git apply -v --ignore-whitespace {}".format(patch)) != 0:
            LOGGER.critical("Applying {} FAILED...".format(patch))
            return None

    LOGGER.info("Successful update")
    return (cube_remote_version, header_remote_version, header_remote_date)


with ThreadPool(len(stm32_families)) as pool:
    family_versions = pool.map(get_header_files, stm32_families)


def update_readme(readme, family, new_version, new_date, new_cube):
    match = r"{0}: v.+? created .+? \(Cube{0} v.+?\)".format(family.upper())
    replace = "{0}: v{1} created {2} (Cube{0} v{3})".format(
                    family.upper(), new_version, new_date, new_cube)
    return re.sub(match, replace, readme)

for family, versions in zip(stm32_families, family_versions):
    if versions is None or versions[1] is None: continue;
    readme = update_readme(readme, family, versions[1], versions[2], versions[0])

Path("README.md").write_text(readme)
exit(family_versions.count(None))
