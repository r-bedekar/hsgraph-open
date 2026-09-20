"""Explicitly synthetic software fixtures, not real classification evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hsgraph_release as h


def seal(r):
    return dict(r,derivative_sha256=h.digest(r))


def fixture(root):
    c=root/'candidate';c.mkdir()
    names=['processes','exchanges','boundaries','provider-links','hs2022-identity',
           'mapping-revisions','mapping-projections','owner-decisions','identity-assessments',
           'usitc-legal-excerpts','smoke1','smoke2','supporting-records',
           'reference-records','reference-substitutions']
    d={n+'.jsonl':[] for n in names}
    d['processes.jsonl']=[{'id':'p1','native':{'name':'Synthetic process A'}},{'id':'p2','native':{'name':'Synthetic process B'}}]
    d['exchanges.jsonl']=[{'id':'e1','process_id':'p1','native':{'amount':1}},
                         {'id':'e2','process_id':'p2','native':{'amount':2}}]
    d['provider-links.jsonl']=[{'id':'e1','process_id':'p1','target_process_id':'p2',
       'traversable':True,'traversal_stops':[],'provider_exchange_ids':['e2']}]
    d['hs2022-identity.jsonl']=[{'id':'h','code':'2523','edition':'2022','parent_code':None},
                              {'id':'h6','code':'252310','edition':'2022','parent_code':'2523'}]
    d['mapping-revisions.jsonl']=[{'id':'r1'}]
    d['mapping-projections.jsonl']=[{'id':'m'+str(i),'mapping_id':'r1','process_id':'p'+str(i),
        'exchange_id':'e'+str(i),'review_status':'accepted','mechanical_outcome':'conflicting',
        'target':{'code':'2523','edition':'2022','public_identity_cross_reference':'h',
                  'original_private_identity_id':'original-h'}} for i in (1,2)]
    d['owner-decisions.jsonl']=[{'mapping_id':'r1','decision':'accept','binding':{'exchange_ids':['e1']}}]
    d['identity-assessments.jsonl']=[{'assessment_id':'a1','scope':{'exchange_ids':['e1']},
                                    'claim_type':'product_identity','automated_outcome':'automated_supported'}]
    d['usitc-legal-excerpts.jsonl']=[{'id':'synthetic-rule','source_id':'synthetic',
        'locator':'synthetic p1','content':'Synthetic legal text, not a real rule.',
        'passage_sha256':h.digest('Synthetic legal text, not a real rule.')}]
    d['smoke1.jsonl']=[{'assessment_id':'s1','case_id':'synthetic-cement',
        'scope':{'instance_id':'e1','process_id':'p1'},'mechanical_outcome':'conflicting',
        'assessor':{'outcome':'supported','proposed_target':{'code':'2523','edition':'2022'}},
        'post_run_concerns':['Synthetic unresolved concern'] }]
    artifacts={}
    for name,records in d.items():
        content=b''.join(h.canonical(seal(r))+b'\n' for r in records)
        (c/name).write_bytes(content)
        artifacts[name]={'sha256':h.file_hash(c/name),'bytes':len(content),'records':len(records)}
    m={'schema_version':'selective-release-1','artifacts':artifacts,
       'counts':{k:v['records'] for k,v in artifacts.items()}}
    m['content_sha256']=h.digest(m);(c/'manifest.json').write_bytes(h.canonical(m))
    envelope(root,m['content_sha256'])
    return m['content_sha256']


def envelope(root,sha):
    files={p.relative_to(root).as_posix():{'sha256':h.file_hash(p),'bytes':p.stat().st_size}
           for p in root.rglob('*') if p.is_file() and p.parent!=root}
    m={'schema_version':'hsgraph-release-envelope-1','files':files,'candidate_content_sha256':sha}
    m['content_sha256']=h.digest(m);(root/'manifest.json').write_bytes(h.canonical(m))
    sums=''.join(h.file_hash(root/n)+'  '+n+'\n' for n in sorted(set(files)|{'manifest.json'}))
    (root/'SHA256SUMS').write_text(sums)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'package';self.root.mkdir()
        self.sha=fixture(self.root)

    def loaded(self):
        path=self.base/'index.sqlite'
        h.load_package(self.root,path,self.sha)
        store=h.Store(path);self.addCleanup(store.close)
        return store

    def test_hash_order_and_material_change(self):
        self.assertEqual(h.digest({'b':1,'a':2}),h.digest({'a':2,'b':1}))
        self.assertNotEqual(h.digest({'a':1}),h.digest({'a':2}))

    def test_package_verifies_without_private_inputs(self):
        self.assertEqual(h.verify_package(self.root,self.sha)['status'],'passed')

    def test_wrong_frozen_snapshot_rejected(self):
        with self.assertRaises(ValueError):h.verify_package(self.root,h.FROZEN)

    def test_changed_artifact_rejected(self):
        with (self.root/'candidate/exchanges.jsonl').open('a') as f:f.write('{}\n')
        with self.assertRaises(ValueError):h.verify_package(self.root,self.sha)

    def test_extra_file_rejected(self):
        (self.root/'extra.txt').write_text('synthetic')
        with self.assertRaises(ValueError):h.verify_package(self.root,self.sha)

    def test_symlink_rejected(self):
        (self.root/'link').symlink_to(self.root/'manifest.json')
        with self.assertRaises(ValueError):h.verify_package(self.root,self.sha)

    def test_missing_checksum_entry_rejected(self):
        (self.root/'SHA256SUMS').write_text('')
        with self.assertRaises(ValueError):h.verify_package(self.root,self.sha)

    def test_index_refuses_overwrite(self):
        self.loaded()
        with self.assertRaises(ValueError):h.load_package(self.root,self.base/'index.sqlite',self.sha)

    def test_store_rebuild_content_deterministic(self):
        a=h.load_package(self.root,self.base/'a.sqlite',self.sha)
        b=h.load_package(self.root,self.base/'b.sqlite',self.sha)
        self.assertEqual(a['store_content_sha256'],b['store_content_sha256'])

    def test_original_catalogue_binding_unchanged(self):
        s=self.loaded();r=s.hs('2523','exploratory')['mapping_projections'][0]
        self.assertEqual(r['target']['original_private_identity_id'],'original-h')

    def test_owner_scope_not_inherited_from_accepted_label(self):
        s=self.loaded()
        self.assertEqual(len(s.hs('2523','owner')['mapping_projections']),1)
        self.assertEqual(s.review('e2')['state'],'no_owner_acceptance')

    def test_specialist_default_empty(self):
        self.assertEqual(self.loaded().hs('2523')['mapping_projections'],[])

    def test_no_hs4_to_hs6_expansion(self):
        self.assertEqual(self.loaded().hs('252310','exploratory')['mapping_projections'],[])

    def test_automated_claims_do_not_require_owner_acceptance(self):
        s=self.loaded();r=s.hs('2523','automated')
        self.assertEqual(len(r['automated_hs_cases']),1)
        self.assertEqual(r['mapping_projections'],[])

    def test_mechanical_automated_and_concern_remain_separate(self):
        r=self.loaded().case('smoke1','synthetic-cement')
        self.assertEqual(r['mechanical_outcome'],'conflicting')
        self.assertEqual(r['automated_hs_outcome'],'supported')
        self.assertTrue(r['post_run_concerns'])

    def test_identity_not_promoted_to_hs(self):
        s=self.loaded();self.assertEqual(s.instance('e1')['product_identity_assessments'][0]['claim_type'],'product_identity')
        self.assertEqual(len(s.hs('2523','automated')['automated_hs_cases']),1)

    def test_trace_uses_recorded_provider_and_no_quantities(self):
        r=self.loaded().trace('p1')
        self.assertEqual(r['paths'][0]['process_ids'],['p1','p2'])
        self.assertFalse(r['quantities_calculated']);self.assertFalse(r['supplier_claim'])

    def test_trace_does_not_join_matching_hs(self):
        self.assertEqual(self.loaded().trace('p2')['paths'],[])

    def test_zero_depth_and_depth_bound(self):
        s=self.loaded();self.assertEqual(s.trace('p1',0)['paths'],[])
        with self.assertRaises(ValueError):s.trace('p1',21)

    def test_stored_stop_not_overridden_by_review(self):
        s=self.loaded();s.close()
        with sqlite3.connect(self.base/'index.sqlite') as c:
            payload=json.loads(c.execute("SELECT payload FROM records WHERE artifact='provider-links.jsonl'").fetchone()[0])
            payload.update(traversable=False,traversal_stops=['unevaluated_formula'])
            c.execute("UPDATE records SET payload=? WHERE artifact='provider-links.jsonl'",(json.dumps(payload),))
        s=h.Store(self.base/'index.sqlite');self.addCleanup(s.close)
        r=s.trace('p1');self.assertEqual(r['paths'],[]);self.assertTrue(r['gaps'])

    def test_legal_citation_match_is_separate_from_support(self):
        e={'id':'law','source_id':'source','locator':'p1','passage_sha256':'abc'}
        h.citations({'legal_citations':[dict(e,evidence_id='law')]},{'law':e})
        with self.assertRaises(ValueError):h.citations({'legal_citations':[{'evidence_id':'absent'}]},{'law':e})

    def test_archive_hash_and_fresh_destination(self):
        archive=self.base/'synthetic.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('hello.txt','synthetic')
        with self.assertRaises(ValueError):h.unpack(archive,self.base/'out','wrong')
        h.unpack(archive,self.base/'out',h.file_hash(archive))
        with self.assertRaises(ValueError):h.unpack(archive,self.base/'out',h.file_hash(archive))

    def test_archive_traversal_and_duplicate_rejected(self):
        for name in ['../escape','/absolute','a/../escape','a\\escape']:
            archive=self.base/'unsafe.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr(name,'synthetic')
            with self.subTest(name=name),self.assertRaises(ValueError):
                h.unpack(archive,self.base/'out',h.file_hash(archive))


if __name__=='__main__':unittest.main()
