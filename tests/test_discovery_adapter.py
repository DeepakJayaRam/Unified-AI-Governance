"""Synthetic manifests are explicit test fixtures, never seeded product results."""
import os
import tempfile
from copy import deepcopy

import pytest

from integrations.discovery import ADAPTERS, validate_scan_input


def fixture_input():
    manifest={'name':'uag-test-fixture','version':'1.0.0','dependencies':{'openai':'6.8.1'}}
    return {'package_json':manifest,'package_lock':{'name':manifest['name'],'version':'1.0.0','lockfileVersion':3,
            'packages':{'':deepcopy(manifest),'node_modules/openai':{'version':'6.8.1','license':'Apache-2.0'}}}}


@pytest.mark.parametrize('change',[ 'scripts','url','traversal','dot_path','root_mismatch','arbitrary_path'])
def test_reject_unsafe_input(change):
    data=fixture_input()
    if change=='scripts':data['package_json']['scripts']={'install':'echo unsafe'}
    if change=='url':data['package_lock']['packages']['node_modules/openai']['resolved']='http://127.0.0.1/private'
    if change=='traversal':data['package_lock']['packages']['../private']={'version':'1.0.0'}
    if change=='dot_path':data['package_lock']['packages']['node_modules/..']={'version':'1.0.0'}
    if change=='root_mismatch':data['package_lock']['packages']['']['name']='different'
    if change=='arbitrary_path':data['path']='C:/Users'
    with pytest.raises(ValueError):validate_scan_input(data)


def test_manifest_only_is_rejected_instead_of_claiming_complete_inventory():
    with pytest.raises(ValueError):validate_scan_input({'package_json':fixture_input()['package_json']})


def test_cancelled_scan_never_executes():
    result=ADAPTERS['cdxgen'].execute(fixture_input(),{},cancelled=lambda:True)
    assert result.status=='failed' and result.error['code']=='cancelled'


def test_config_rejects_host_command_and_timeout_abuse():
    for value in ({'command':'anything'},{'timeout_seconds':500},{'timeout_seconds':True}):
        with pytest.raises(ValueError):ADAPTERS['cdxgen'].validate_config(value)


@pytest.mark.skipif(os.environ.get('UAG_TEST_CDXGEN')!='1',reason='Requires explicitly installed cdxgen and supported Node')
def test_real_cdxgen_inventory(tmp_path,monkeypatch):
    staging_root=tmp_path/'a directory with spaces'
    staging_root.mkdir()
    monkeypatch.setattr(tempfile,'tempdir',str(staging_root))
    if not os.environ.get('UAG_SCAN_TMP_ROOT'):
        pytest.skip('Set no-space UAG_SCAN_TMP_ROOT to test from a workspace containing spaces')
    result=ADAPTERS['cdxgen'].execute(fixture_input(),{})
    assert result.status=='succeeded',result.model_dump()
    assert result.raw_output['bom']['bomFormat']=='CycloneDX'
    assert result.normalized['bom']==result.raw_output['bom']
    assert result.normalized['component_count']==1
    assert result.normalized['components'][0]['name']=='openai'
    assert result.normalized['components'][0]['version']=='6.8.1'
    assert result.provenance['version']=='13.7.0'
    assert len(result.provenance['artifact_sha256'])==64


def test_health_rejects_unsupported_temp_directory(tmp_path,monkeypatch):
    staging_root=tmp_path/'directory with spaces'
    staging_root.mkdir()
    monkeypatch.setenv('UAG_SCAN_TMP_ROOT',str(staging_root))
    health=ADAPTERS['cdxgen'].health({})
    assert health['status']=='not_configured'
    assert 'UAG_SCAN_TMP_ROOT' in health['detail']
