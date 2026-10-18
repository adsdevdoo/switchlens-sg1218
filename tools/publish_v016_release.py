#!/usr/bin/env python3
"""Verify the tested v0.1.6 package and publish it without replacing any asset.

--verify-only performs local integrity checks and never contacts GitHub.
Publication is restricted to this repository/tag and the checked-out commit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parents[1]
REPO = 'adsdevdoo/switchlens-sg1218'
TAG = 'v0.1.6'
BIN = 'SwitchLens-SG1218MPE-V5-v0.1.6.bin'
EXPECTED = '239a0127fa9ddbb72e55da992ca79c46cb9435888f7c23a82f08e42718a8ad46'
TESTED_COMMIT = 'f3481b37b0decf54317c8b8f6193fd7f745934d7'
TEST_RUN = 39144589077
FOLDER = ROOT / 'releases' / TAG
REPORTS = {'anonymous-http-test-results.json': 9, 'target-test-results.json': 11,
           'manual-cooling-test-results.json': 6, 'security-test-results.json': 5,
           'release-path-test-results.json': 4}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    names = [BIN, 'SHA256SUMS', 'build-manifest.json', 'validation.json',
             'README.md', 'README.ru.md', *REPORTS]
    files = {name: (FOLDER / name).read_bytes() for name in names}
    files['Test-AnonymousStats.ps1'] = (ROOT / 'tools/Test-AnonymousStats.ps1').read_bytes()
    image = files[BIN]
    assert digest(image) == EXPECTED and len(image) == 1013324
    assert int.from_bytes(image[:4], 'big') == zlib.crc32(image[0x10:0xf7000]) == 0x8c15e140
    assert files['SHA256SUMS'].decode().split() == [EXPECTED, BIN]
    manifest = json.loads(files['build-manifest.json'])
    assert manifest['output_sha256'] == EXPECTED and manifest['version'] == TAG
    for key in ('uart_cli', 'cooling_cli', 'anonymous_stats', 'vendor_udp_management_disabled'):
        assert manifest[key] is True, key
    assert manifest['hardware_boot_test'] is False
    assert digest((ROOT / 'tools/build_firmware.py').read_bytes()) == manifest['build_recipe_sha256']
    for path, sha in manifest['sources_sha256'].items():
        assert digest((ROOT / path).read_bytes()) == sha, 'Untested source: ' + path
    for name, count in REPORTS.items():
        report = json.loads(files[name])
        assert report['image_sha256'] == EXPECTED
        assert (report['tests'], report['failures'], report['errors']) == (count, 0, 0), name
    validation = json.loads(files['validation.json'])
    assert validation['source_commit'] == TESTED_COMMIT
    assert validation['validation_run'] == TEST_RUN
    assert validation['image_sha256'] == EXPECTED
    assert validation['mips_test_methods'] == sum(REPORTS.values()) == 35
    assert validation['hardware_verified'] is False
    assert validation['v015_hardware_verified'] is False
    print('Package/source verification: PASS; SHA-256 ' + EXPECTED)
    return files


def publish(files):
    assert os.environ['GH_REPOSITORY'] == REPO
    commit = os.environ['GH_COMMIT']
    assert re.fullmatch(r'[0-9a-f]{40}', commit)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == commit
    token = os.environ['GH_TOKEN']
    api = 'https://api.github.com/repos/' + REPO

    def request(url, method='GET', data=None, raw=False, content_type=None):
        assert urllib.parse.urlparse(url).hostname in ('api.github.com', 'uploads.github.com')
        headers = {'Authorization': 'Bearer ' + token,
                   'Accept': 'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'SwitchLens-v016-release'}
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            content_type = 'application/json'
        if content_type:
            headers['Content-Type'] = content_type
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response:
            content = response.read()
        return content if raw else json.loads(content)

    def optional(url):
        try:
            return request(url)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            return None

    # Recheck the successful run before creating a tag or release.
    run = request(api + '/actions/runs/' + str(TEST_RUN))
    assert run['head_sha'] == TESTED_COMMIT and run['conclusion'] == 'success'
    tag_ref = optional(api + '/git/ref/tags/' + TAG)
    if tag_ref:
        assert tag_ref['object']['type'] == 'commit' and tag_ref['object']['sha'] == commit, 'Existing tag differs'

    base = 'https://github.com/' + REPO + '/blob/' + commit + '/releases/' + TAG + '/'
    notes = re.sub(r'\]\(([^)]+)\)', lambda m: '](' + urllib.parse.urljoin(base, m.group(1)) + ')',
                   files['README.md'].decode())
    release = optional(api + '/releases/tags/' + TAG)
    if release is None:
        # Resume a draft left by a failed upload without replacing any asset.
        releases = request(api + '/releases?per_page=100')
        release = next((r for r in releases if r['tag_name'] == TAG), None)
    if release is None:
        release = request(api + '/releases', 'POST', {
            'tag_name': TAG, 'target_commitish': commit,
            'name': 'SwitchLens v0.1.6 — session-independent statistics',
            'body': notes, 'draft': True, 'prerelease': True, 'make_latest': 'false'})
    else:
        assert release['target_commitish'] == commit, 'Existing release targets another commit'
        assert release['body'] == notes, 'Existing release notes differ'
    upload = release['upload_url'].split('{')[0]
    existing = {asset['name']: asset for asset in release['assets']}
    for name, content in files.items():
        expected = 'sha256:' + digest(content)
        if name in existing:
            assert existing[name].get('digest') == expected, 'Existing asset differs: ' + name
            continue
        assert release['draft'], 'Refusing to change published assets'
        asset = request(upload + '?' + urllib.parse.urlencode({'name': name}), 'POST',
                        data=content, content_type='application/octet-stream')
        assert asset['digest'] == expected, name
    if release['draft']:
        release = request(api + '/releases/' + str(release['id']), 'PATCH',
                          {'draft': False, 'prerelease': True, 'make_latest': 'false'})
    ref = request(api + '/git/ref/tags/' + TAG)
    assert ref['object']['type'] == 'commit' and ref['object']['sha'] == commit
    print('Published: ' + release['html_url'])
    print('Release commit: ' + commit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    package = verify()
    if not args.verify_only:
        publish(package)
