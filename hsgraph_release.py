"""HSGraph v0.1.0 offline release reader. No inference, model or network calls.

The SQLite store is a disposable index of published JSONL, not a reconstruction
of the private scientific snapshots. Saved claim objects and outcomes are kept.
"""
import argparse
from collections import Counter, deque
from contextlib import closing
import hashlib
import json
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import sys
import zipfile

VERSION = '0.1.0'
FROZEN = '78b9a1f0afbad1ae0b7ef81e63af5d03c49cc79eb99a09ac853840e23bdca710'
FORMAT = 'hsgraph-public-index-1'
MAX_PACKAGE_BYTES = 1024 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def safe_name(name):
    p = PurePosixPath(name)
    require(isinstance(name, str) and name and not p.is_absolute() and
            '\\' not in name and ':' not in name and
            all(part not in ('', '.', '..') for part in name.split('/')), 'Unsafe package path')
    return name


def unpack(archive, destination, expected_sha256):
    """Hash first; reject traversal, links, duplicates and excessive expansion."""
    require(file_hash(archive) == expected_sha256, 'Archive SHA-256 mismatch')
    destination = Path(destination)
    require(not destination.exists(), 'Extraction requires a fresh directory')
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [safe_name(i.filename) for i in infos]
        require(len(names) == len(set(names)) and len(names) <= 100, 'Duplicate/excess package members')
        require(sum(i.file_size for i in infos) <= MAX_PACKAGE_BYTES, 'Package too large')
        for i in infos:
            mode = i.external_attr >> 16
            require(not i.is_dir() and not stat.S_ISLNK(mode) and
                    (stat.S_IFMT(mode) in (0, stat.S_IFREG)), 'Non-file package member')
        destination.mkdir(parents=True)
        for i in infos:
            target = destination / i.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as source, target.open('xb') as output:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    output.write(block)
    return {'status': 'extracted', 'files': len(infos), 'archive_sha256': expected_sha256}


def check_seal(value, key):
    body = dict(value)
    claimed = body.pop(key)
    require(digest(body) == claimed, 'Content hash mismatch: ' + key)
    return claimed


def actual_files(root):
    result = set()
    for p in Path(root).rglob('*'):
        require(not p.is_symlink(), 'Symlink in package')
        if p.is_file():
            result.add(p.relative_to(root).as_posix())
    return result


def citations(value, legal):
    if isinstance(value, dict):
        for c in value.get('legal_citations', []):
            e = legal.get(c.get('evidence_id'))
            require(e and all(c.get(k) == e[k] for k in ('source_id', 'locator', 'passage_sha256')),
                    'Legal citation does not match supplied evidence')
        for v in value.values():
            citations(v, legal)
    elif isinstance(value, list):
        for v in value:
            citations(v, legal)


def rows(candidate, name):
    with (Path(candidate) / name).open(encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def verify_candidate(candidate, expected=FROZEN):
    candidate = Path(candidate)
    m = read_json(candidate / 'manifest.json')
    seal = check_seal(m, 'content_sha256')
    require(expected is None or seal == expected, 'Not the frozen release candidate')
    require(m['schema_version'] == 'selective-release-1', 'Unsupported candidate format')
    require(actual_files(candidate) == set(m['artifacts']) | {'manifest.json'}, 'Unexpected/missing candidate files')
    data = {}
    for name, info in m['artifacts'].items():
        require(safe_name(name) == Path(name).name, 'Candidate artifacts must be flat')
        require(file_hash(candidate/name) == info['sha256'] and
                (candidate/name).stat().st_size == info['bytes'], 'Artifact bytes differ: '+name)
        if name.endswith('.jsonl'):
            records = list(rows(candidate, name))
            require(len(records) == info['records'], 'Record count mismatch')
            for r in records:
                check_seal(r, 'derivative_sha256')
            ids = [r.get('id', r.get('assessment_id', str(i))) for i,r in enumerate(records)]
            require(len(ids) == len(set(ids)), 'Duplicate artifact identity')
            data[name] = records
    ps = {r['id']:r for r in data['processes.jsonl']}
    es = {r['id']:r for r in data['exchanges.jsonl']}
    bs = {r['id'] for r in data['boundaries.jsonl']}
    for e in es.values():
        require(e['process_id'] in ps, 'Exchange process missing')
    for p in data['provider-links.jsonl']:
        target = p.get('target_process_id')
        require(p['id'] in es and p['process_id'] in ps, 'Provider subject missing')
        require(target is None or target in set(ps)|bs, 'Provider target missing')
        require(all(i in es for i in p.get('provider_exchange_ids', [])), 'Provider exchange missing')
        require(not p['traversable'] or (target in ps and not p.get('traversal_stops')),
                'Traversable boundary or unresolved link')
    identities = {r['id']:r for r in data['hs2022-identity.jsonl']}
    codes = {r['code'] for r in identities.values()}
    for r in identities.values():
        require(r['parent_code'] is None or r['parent_code'] in codes, 'HS parent missing')
    revisions = {r['id'] for r in data['mapping-revisions.jsonl']}
    for r in data['mapping-projections.jsonl']:
        require(r['exchange_id'] in es and r['process_id'] in ps and r['mapping_id'] in revisions,
                'Projection dependency missing')
        if r.get('target'):
            cross = r['target'].get('public_identity_cross_reference')
            require(cross in identities and identities[cross]['code'] == r['target']['code'] and
                    identities[cross]['edition'] == r['target']['edition'], 'HS cross-reference missing')
    for r in data['owner-decisions.jsonl']:
        require(set(r['binding']['exchange_ids']) <= set(es) and r['mapping_id'] in revisions,
                'Owner binding dependency missing')
    for r in data['identity-assessments.jsonl']:
        require(set(r['scope']['exchange_ids']) <= set(es), 'Identity claim scope missing')
    legal = {r['id']:r for r in data['usitc-legal-excerpts.jsonl']}
    for r in legal.values():
        require(digest(r['content']) == r['passage_sha256'], 'Legal passage changed')
    for name in ('smoke1.jsonl','smoke2.jsonl'):
        for r in data[name]:
            require(r['scope']['instance_id'] in es, 'Smoke instance missing')
            citations(r, legal)
    # Published D6 references are a measurement subgraph, not density conversions.
    refs = {r['id']:r for r in data.get('reference-records.jsonl', [])}
    units = {u['id']:(r['id'],u) for r in refs.values() for u in r.get('units', [])}
    for r in refs.values():
        if r['kind'] == 'quantity':
            require(r['unit_group_id'] in refs and r['reference_unit_id'] in units, 'Quantity dependency missing')
        else:
            require(r['quantity_id'] in refs and r['reference_unit_id'] in units, 'Unit group dependency missing')
    for r in data.get('reference-substitutions.jsonl', []):
        require(r['project_record_id'] in set(refs)|set(units), 'Substitution target missing')
    for e in es.values():
        if 'reference_substitution' in e:
            b = e['reference_substitution']; u = units.get(b['unit_id']); q = refs.get(b['quantity_id'])
            require(u and q and u[0] == q['unit_group_id'] == b['unit_group_id'], 'Measurement reference missing')
            require(e['native']['unit']['@id'] == b['unit_id'] and
                    e['native']['flowProperty']['@id'] == b['quantity_id'], 'Measurement binding mismatch')
    return {'status':'passed', 'candidate_content_sha256':seal, 'artifacts':len(m['artifacts']),
            'records':sum(len(v) for v in data.values()), 'counts':m['counts'],
            'reference_check':'Retained graph and explicit cross-references resolve; private evidence remains unavailable',
            'semantic_support_verified':False, 'model_replay_performed':False}


def verify_package(root, expected_candidate=FROZEN, expected_outer=None):
    root = Path(root)
    m = read_json(root/'manifest.json')
    require(m['schema_version'] == 'hsgraph-release-envelope-1', 'Unknown release envelope')
    outer = check_seal(m, 'content_sha256')
    require(expected_outer is None or expected_outer == outer, 'Unexpected release envelope')
    require(actual_files(root) == set(m['files'])|{'manifest.json','SHA256SUMS'}, 'Unexpected/missing package attachment')
    for name, info in m['files'].items():
        safe_name(name)
        require(file_hash(root/name) == info['sha256'] and (root/name).stat().st_size == info['bytes'],
                'Package file mismatch: '+name)
    expected_sums = ''.join(file_hash(root/n)+'  '+n+'\n' for n in sorted(set(m['files'])|{'manifest.json'}))
    require((root/'SHA256SUMS').read_text() == expected_sums, 'Package checksum list mismatch')
    require(m['candidate_content_sha256'] == expected_candidate, 'Candidate reference changed')
    return dict(verify_candidate(root/'candidate', expected_candidate), envelope_content_sha256=outer)


def store_digest(c):
    h = hashlib.sha256()
    for r in c.execute('SELECT artifact,ordinal,payload FROM records ORDER BY artifact,ordinal'):
        h.update(canonical(list(r)) + b'\n')
    return h.hexdigest()


def load_package(root, store, expected_candidate=FROZEN, expected_outer=None):
    verified = verify_package(root, expected_candidate, expected_outer)
    store = Path(store)
    require(not store.exists(), 'Store exists; use a fresh path')
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open('xb'):
        pass
    with closing(sqlite3.connect(store)) as c, c:
        c.execute('CREATE TABLE records(artifact TEXT,ordinal INTEGER,record_id TEXT,instance TEXT,process TEXT,code TEXT,case_id TEXT,payload TEXT,PRIMARY KEY(artifact,ordinal))')
        c.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
        candidate = Path(root)/'candidate'
        m = read_json(candidate/'manifest.json')
        for name in sorted(m['artifacts']):
            if not name.endswith('.jsonl'):
                continue
            for i,r in enumerate(rows(candidate, name)):
                scope = r.get('scope', {})
                scope = scope if isinstance(scope, dict) else {}
                instance = r.get('exchange_id', scope.get('instance_id'))
                if name == 'exchanges.jsonl': instance = r['id']
                if name == 'identity-assessments.jsonl': instance = scope['exchange_ids'][0]
                target = r.get('target') or {}
                c.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?)',
                    (name,i,r.get('id',r.get('assessment_id',str(i))),instance,
                     r.get('process_id',scope.get('process_id')),r.get('code',target.get('code')),
                     r.get('case_id'),canonical(r).decode()))
        for col in ('record_id','instance','process','code','case_id'):
            c.execute('CREATE INDEX ix_'+col+' ON records('+col+')')
        index_hash = store_digest(c)
        for key,value in {'format':FORMAT,'candidate':expected_candidate,'envelope':verified['envelope_content_sha256'],
                          'store_content_sha256':index_hash}.items():
            c.execute('INSERT INTO metadata VALUES (?,?)',(key,value))
    return dict(verified, store_content_sha256=index_hash,
                operation='indexed retained records; no predicates or model generations executed')


class Store:
    def __init__(self, path):
        self.c = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)
        meta = dict(self.c.execute('SELECT key,value FROM metadata'))
        require(meta.get('format') == FORMAT, 'Not a verified public index')
        self.metadata = meta

    def close(self): self.c.close()

    def get(self, artifact, field=None, value=None):
        require(field in (None,'record_id','instance','process','code','case_id'), 'Unsupported lookup')
        sql = 'SELECT payload FROM records WHERE artifact=?'
        args = [artifact]
        if field:
            sql += ' AND '+field+'=?'; args.append(value)
        return [json.loads(r[0]) for r in self.c.execute(sql+' ORDER BY ordinal',args)]

    def review(self, instance):
        bound = [r for r in self.get('owner-decisions.jsonl') if instance in r['binding']['exchange_ids']]
        return {'state':'owner_accepted' if any(r['decision']=='accept' for r in bound) else 'no_owner_acceptance',
                'specialist_validation':False, 'decisions':bound,
                'meaning':'Exact recorded instance binding only; no chain acceptance or extension from projection labels'}

    def instance(self, instance):
        es = self.get('exchanges.jsonl','record_id',instance)
        require(es, 'Unknown retained exchange')
        e = es[0]
        process = self.get('processes.jsonl','record_id',e['process_id'])[0]
        smoke = {name:self.get(name+'.jsonl','instance',instance) for name in ('smoke1','smoke2')}
        return {'exchange':e,'process':process,
                'mechanical_projections':self.get('mapping-projections.jsonl','instance',instance),
                'product_identity_assessments':self.get('identity-assessments.jsonl','instance',instance),
                'hs_assessments':smoke,'human_review':self.review(instance),
                'layer_warning':'Product identity does not validate HS mapping or production relationships. Saved outcomes are not recomputed.'}

    def case(self, suite, case):
        require(suite in ('smoke1','smoke2'), 'Unknown suite')
        cases = self.get(suite+'.jsonl','case_id',case)
        require(len(cases)==1,'Unknown case')
        r = cases[0]; a = r['assessor']; eid = r['scope']['instance_id']
        return {'suite':suite,'case_id':case,'instance_id':eid,'mechanical_outcome':r['mechanical_outcome'],
                'automated_hs_outcome':a.get('outcome',a.get('hs_resolution')),
                'human_review':self.review(eid),'post_run_concerns':r['post_run_concerns'],
                'record':r,'warning':'Retained development case, not an independent benchmark. Concerns and disagreements are unresolved.'}

    def hs(self, code, mode='specialist'):
        require(code.isdigit() and len(code) in (2,4,6), 'Use exact HS2/4/6 code')
        require(mode in ('specialist','owner','automated','exploratory'), 'Unknown display mode')
        identities = self.get('hs2022-identity.jsonl','code',code)
        require(identities,'Unknown HS2022 code')
        projections = self.get('mapping-projections.jsonl','code',code)
        if mode=='specialist': projections=[]
        elif mode=='owner': projections=[p for p in projections if self.review(p['exchange_id'])['state']=='owner_accepted']
        elif mode=='automated':
            # Automated claim records, not identity assessments promoted to HS support.
            projections=[]
        cases=[]
        if mode in ('automated','exploratory'):
            for suite in ('smoke1','smoke2'):
                for r in self.get(suite+'.jsonl'):
                    target = r['assessor'].get('proposed_target') or {}
                    if target.get('code')==code and target.get('edition')=='2022':
                        cases.append(self.case(suite,r['case_id']))
        return {'code':code,'edition':'2022','mode':mode,'identities':identities,
                'mapping_projections':projections,'automated_hs_cases':cases,
                'warning':'Exact-code browsing, no HS4-to-HS6 expansion. Projections retain their original bindings and are not new accepted classifications.'}

    def trace(self, process, depth=2):
        require(type(depth) is int and 0<=depth<=20,'Depth must be 0..20')
        require(self.get('processes.jsonl','record_id',process),'Unknown retained process')
        queue=deque([(process,[process],[])]);paths=[];gaps={}
        while queue:
            current,nodes,links=queue.popleft()
            if len(links)>=depth: continue
            for link in self.get('provider-links.jsonl','process',current):
                target=link.get('target_process_id')
                if not link['traversable']:
                    gaps[link['id']]=link;continue
                if target in nodes:
                    gaps[link['id']]=dict(link,traversal_stop='cycle');continue
                require(self.get('processes.jsonl','record_id',target),'Unexplained target gap')
                nn=nodes+[target];nl=links+[link]
                paths.append({'process_ids':nn,'provider_links':nl,
                              'relationship_assessment':'Not established by starting mapping/identity or owner acceptance'})
                require(len(paths)<=10000,'Trace exceeds 10000 paths; reduce depth')
                queue.append((target,nn,nl))
        return {'process_id':process,'depth':depth,'semantics':'modeled_default_provider_paths',
                'paths':paths,'gaps':list(gaps.values()),'quantities_calculated':False,
                'technical_validity':'unreviewed','supplier_claim':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',action='version',version=VERSION)
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('unpack');x.add_argument('archive');x.add_argument('destination');x.add_argument('--sha256',required=True)
    for name in ('verify','load'):
        x=sub.add_parser(name);x.add_argument('package')
        if name=='load':x.add_argument('--store',required=True)
    for name in ('case','hs','instance','trace','verify-store','record'):
        x=sub.add_parser(name);x.add_argument('--store',required=True)
        if name=='case':x.add_argument('suite',choices=['smoke1','smoke2']);x.add_argument('case_id')
        if name=='hs':x.add_argument('code');x.add_argument('--mode',choices=['specialist','owner','automated','exploratory'],default='specialist')
        if name=='instance':x.add_argument('instance_id')
        if name=='trace':x.add_argument('process_id');x.add_argument('--depth',type=int,default=2)
        if name=='record':x.add_argument('artifact');x.add_argument('record_id')
    a=p.parse_args(argv)
    try:
        if a.command=='unpack': result=unpack(a.archive,a.destination,a.sha256)
        elif a.command in ('verify','load'):
            public_manifest=read_json(Path(__file__).with_name('release-manifest.json'))
            outer=public_manifest['envelope_content_sha256']
            result=verify_package(a.package,expected_outer=outer) if a.command=='verify' else load_package(a.package,a.store,expected_outer=outer)
        else:
            with closing(Store(a.store)) as s:
                require(s.metadata['candidate']==FROZEN,'Wrong candidate index')
                if a.command=='case':result=s.case(a.suite,a.case_id)
                elif a.command=='hs':result=s.hs(a.code,a.mode)
                elif a.command=='instance':result=s.instance(a.instance_id)
                elif a.command=='trace':result=s.trace(a.process_id,a.depth)
                elif a.command=='record':result=s.get(a.artifact,'record_id',a.record_id)
                else:
                    require(store_digest(s.c)==s.metadata['store_content_sha256'],'Store content changed')
                    result={'status':'passed',**s.metadata}
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,KeyError,OSError,sqlite3.Error,zipfile.BadZipFile) as exc:
        print('Error: '+str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
