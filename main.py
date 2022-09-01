import hashlib
import json
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
from os.path import join, dirname, exists

import UnityPy
import brotli
import requests

script_dir = dirname(__file__)

HEADER = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 XL Build/QQ3A.200805.001)"}

initial_version = {"TruthVersion": "00080018", "hash": "b3262028ee29ee9cfe7229ecdc865a5c"}

version = {}


def _validate(truth_version):
    # Check if the TruthVersion exists
    r = requests.get(
        f"https://img-pc.so-net.tw/dl/Resources/{truth_version}"
        f"/Jpn/AssetBundles/Android/manifest/masterdata2_assetmanifest",
        headers=HEADER,
    )

    if r.status_code != 200:
        logging.info(f"TruthVersion {truth_version} is not exist.")
        return
    logging.info(f"TruthVersion {truth_version} is exist.")

    filename, path, _, size, _ = r.text.split(",")

    version.update({
        'TruthVersion': truth_version,
        'path': path,
        'size': size
    })
    return True


def download(path, size, truth_version):
    logging.info(f"Downloading asset bundle ...")
    r = requests.get(f"https://img-pc.so-net.tw/dl/pool/AssetBundles/{path[:2]}/{path}", headers=HEADER)

    if r.headers.get("Content-Length") != size:
        logging.info("Size is not same, but it may be fine")

    with open(join(script_dir, "masterdata_master.unity3d"), "wb+") as f:
        f.write(r.content)

    master_db = None
    global version
    # Unpack asset bundle
    with open(join(script_dir, "masterdata_master.unity3d"), "rb") as f:
        bundle = UnityPy.load(f)

        for obj in bundle.objects:
            if obj.type == obj.type.TextAsset:
                data = obj.read()
                master_db = data.m_Script
                break

    os.remove(join(script_dir, "masterdata_master.unity3d"))

    # Compress
    logging.info("Compressing redive_tw.db.br ...")
    brotli_db = brotli.compress(master_db)

    # Hash Check
    logging.info("Generating MD5 Hash ...")
    new_hash = hashlib.md5(brotli_db).hexdigest()

    if exists(join(script_dir, "out", "version.json")):
        with open(join(script_dir, "out", "version.json")) as f:
            old_version = json.load(f)
    else:
        old_version = initial_version

    if old_version.get("hash") == new_hash:
        logging.warning("Database Hashes are same")
        return
    logging.info(f"Old Hash: {old_version.get('hash')} ({old_version.get('TruthVersion')})")
    logging.info(f"New Hash: {new_hash} ({truth_version})")

    # Save
    if exists(join(script_dir, "out", "redive_tw.db")):
        shutil.copyfile(join(script_dir, "out", "redive_tw.db"), join(script_dir, "out", "prev.redive_tw.db"))

    with open(join(script_dir, "out", "redive_tw.db.br"), "wb") as f:
        f.write(brotli_db)

    with open(join(script_dir, "out", "redive_tw.db"), "wb") as f:
        f.write(master_db)

    version.update({'hash': new_hash})

    with open(join(script_dir, "out", "version.json"), "w") as f:
        json.dump({'TruthVersion': version['TruthVersion'], 'hash': version['hash']}, f)
    logging.info('Wrote out new TruthVersion and hash.')

    logging.info("Done")


def guess(end_if_true=False, max_try=20):
    logging.info("Start guessing TruthVersion")
    if exists(join(script_dir, "out", "version.json")):
        with open(join(script_dir, "out", "version.json")) as f:
            old_version = json.load(f)
            version.update(old_version)
    else:
        old_version = initial_version
    last_ver = old_version.get("TruthVersion")
    logging.info(f"Last Version: {last_ver}")
    big, small = int(last_ver[:5]), int(last_ver[6:]) + 1
    try_count = 0
    while try_count < max_try:
        if _validate(f"{big:05d}0{small:02d}"):
            if end_if_true:
                break
        if small >= 20:
            big += 1
            small = 0
        else:
            small += 1
        try_count += 1
    logging.info("End guess")


def update():
    guess()
    if exists(join(script_dir, "out", "version.json")):
        with open(join(script_dir, "out", "version.json"), "r") as f:
            last_version = json.load(f)
            if int(version['TruthVersion']) > int(last_version['TruthVersion']):
                download(version['path'], version['size'], version['TruthVersion'])
                return
            else:
                logging.info('No update found.')
                return
    else:
        logging.info('No version record found. Starting initialization.')
        version.update(initial_version)
        with open(join(script_dir, "out", "version.json"), 'w') as f:
            json.dump({'TruthVersion': version['TruthVersion'], 'hash': version['hash']}, f)


if __name__ == "__main__":
    FORMAT = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT,
                        handlers=[RotatingFileHandler(join(script_dir, "redive.log"), maxBytes=1 * 1024 * 1024),
                                  logging.StreamHandler()])
    update()
