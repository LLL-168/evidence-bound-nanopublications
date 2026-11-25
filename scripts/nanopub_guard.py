#!/usr/bin/env python3
"""Check claim/evidence ledgers and export local unsigned nanopublications."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
import uuid

NP_NS='http://www.nanopub.org/nschema#'
VOCAB_NS='urn:litnp:vocab:'
RELATION_FILE=Path(__file__).resolve().parents[1]/'resources/relations.json'
NUMBER=re.compile(r'(?<![A-Za-z0-9_])[-+]?(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][-+]?\d+)?')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def nonempty(value):
    return isinstance(value,str) and bool(value.strip())


def normalized(value):
    return ' '.join(value.split())


def numbers(value):
    value=unicodedata.normalize('NFKC',value).replace('−','-').replace('–','-')
    return set(NUMBER.findall(value))


def absolute_iri(value):
    return nonempty(value) and bool(re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',value)) and not re.search(r'[\s<>"{}|\\^`]',value)


def issue(rule,identifier,message,**extra):
    return {'rule':rule,'id':identifier,'message':message,**extra}


def records(value,label,failures,empty=False):
    if not isinstance(value,list) or not value and not empty:
        failures.append(issue('schema',None,f'{label} must be a list'+('' if empty else ' with records')))
        return []
    result=[]
    for record in value:
        if not isinstance(record,dict) or not nonempty(record.get('id')):
            failures.append(issue('schema',None,f'{label} record needs nonempty id'))
        else:
            result.append(record)
    for key,count in Counter(r['id'] for r in result).items():
        if count>1:
            failures.append(issue('duplicate_id',key,f'{label} contains duplicate IDs'))
    return result


def audit(data):
    failures,reviews,pending=[],[],[]
    report={'status':'fail','failures':failures,'review_candidates':reviews,'excluded_candidates':pending,
            'limits':['No scientific entailment/atomicity/confidence score is computed.',
                      'Local IDs are not Trusty URIs; no signatures or public publication are performed.']}
    if not isinstance(data,dict) or not nonempty(data.get('case_id')):
        failures.append(issue('case_id',None,'Input object needs nonempty real case_id'))
        return report
    report['case_id']=data['case_id']
    publication=data.get('publication')
    if not isinstance(publication,dict) or not nonempty(publication.get('creator')):
        failures.append(issue('publication',None,'Actual extraction creator description required'))
    try:
        when=datetime.fromisoformat(publication.get('created_at','').replace('Z','+00:00'))
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError('Timezone missing')
    except (AttributeError,TypeError,ValueError):
        failures.append(issue('publication_time',None,'Actual timezone-aware ISO creation timestamp required'))
    docs=records(data.get('documents'),'documents',failures)
    blocks=records(data.get('blocks'),'blocks',failures,True)
    claims=records(data.get('claims'),'claims',failures,True)
    if failures:
        return report
    di={d['id']:d for d in docs}
    bi={b['id']:b for b in blocks}
    relations=read(RELATION_FILE)['relations']
    for doc in docs:
        did=doc['id']
        if not nonempty(doc.get('path')) or not isinstance(doc.get('sha256'),str) or not re.fullmatch('[a-fA-F0-9]{64}',doc.get('sha256','')):
            failures.append(issue('document_identity',did,'Actual source path and 64-hex SHA-256 required'))
        else:
            try:
                digest=hashlib.sha256()
                with Path(doc['path']).open('rb') as handle:
                    for chunk in iter(lambda:handle.read(1024*1024),b''):
                        digest.update(chunk)
                if digest.hexdigest().lower()!=doc['sha256'].lower():
                    failures.append(issue('source_hash',did,'Actual source bytes do not match ledger hash'))
            except OSError as exc:
                failures.append(issue('source_file',did,f'Source unavailable: {exc}'))
        if not nonempty(doc.get('title')):
            failures.append(issue('metadata',did,'Verified source title required'))
        authors=doc.get('authors')
        if not isinstance(authors,list) or any(not nonempty(a) for a in authors):
            failures.append(issue('metadata',did,'authors must be a list of actual names'))
        year=doc.get('year')
        if year is not None and (not isinstance(year,int) or isinstance(year,bool) or year<1):
            failures.append(issue('metadata',did,'year must be positive integer or null'))
        for key in ('version','identifier'):
            if doc.get(key) is not None and not nonempty(doc[key]):
                failures.append(issue('metadata',did,f'{key} must be nonempty or null'))
        missing=doc.get('metadata_missing',{})
        for key in ('authors','year','version'):
            if not doc.get(key) and (not isinstance(missing,dict) or not nonempty(missing.get(key))):
                failures.append(issue('metadata_reason',did,f'Missing {key} requires a reason'))
    for block in blocks:
        bid=block['id']
        if not isinstance(block.get('document_id'),str) or block['document_id'] not in di:
            failures.append(issue('block_document',bid,'Block document reference does not resolve'))
        if not nonempty(block.get('text')):
            failures.append(issue('block_text',bid,'Exact source text required'))
        loc=block.get('locator')
        if not isinstance(loc,dict) or not any(k in loc for k in ('page','paragraph','offsets','fragments')):
            failures.append(issue('locator',bid,'Actual page/paragraph/offset locator required'))
        elif 'page' in loc and (not isinstance(loc['page'],int) or isinstance(loc['page'],bool) or loc['page']<1):
            failures.append(issue('locator',bid,'PDF page must be a positive 1-based integer'))
    for claim in claims:
        cid=claim['id']
        if not isinstance(claim.get('document_id'),str) or claim['document_id'] not in di:
            failures.append(issue('claim_document',cid,'Claim source document reference does not resolve'))
        if not nonempty(claim.get('text')):
            failures.append(issue('claim_text',cid,'Nonempty atomic qualified claim text required'))
        for key in ('subject','object'):
            entity=claim.get(key)
            if not isinstance(entity,dict) or not nonempty(entity.get('label')):
                failures.append(issue('entity',cid,f'{key} requires a label'))
            elif entity.get('iri') is not None and not absolute_iri(entity['iri']):
                failures.append(issue('entity_iri',cid,f'{key} IRI must be an actual absolute identifier or omitted'))
        if not isinstance(claim.get('relation'),str) or claim['relation'] not in relations:
            failures.append(issue('relation',cid,'Relation must be in the explicit local controlled vocabulary'))
        if claim.get('polarity') not in ('affirmed','negated'):
            failures.append(issue('polarity',cid,'Explicit affirmed/negated polarity required'))
        if claim.get('modality') not in ('observed','suggested','hypothesis'):
            failures.append(issue('modality',cid,'Explicit observed/suggested/hypothesis modality required'))
        conditions=claim.get('conditions')
        if not isinstance(conditions,list) or any(not nonempty(c) for c in conditions):
            failures.append(issue('conditions',cid,'conditions must be a list of nonempty strings'))
        if claim.get('origin') not in ('reported','author_interpretation','inference'):
            failures.append(issue('origin',cid,'Explicit assertion origin required'))
        if claim.get('origin')=='inference' and not nonempty(claim.get('inference_basis')):
            failures.append(issue('inference_basis',cid,'Extractor inference requires premises/step explanation'))
        status=claim.get('status')
        if status not in ('supported','uncertain','unsupported','conflicted'):
            failures.append(issue('status',cid,'Supported/uncertain/unsupported/conflicted required'))
        elif status!='supported':
            if not nonempty(claim.get('reason')):
                failures.append(issue('status_reason',cid,'Non-supported candidate requires an exact reason'))
            pending.append({'id':cid,'status':status,'reason':claim.get('reason')})
        confidence=claim.get('confidence')
        if not isinstance(confidence,dict) or confidence.get('level') not in ('high','medium','low','undetermined') or not nonempty(confidence.get('basis')):
            failures.append(issue('confidence',cid,'Categorical confidence and actual basis required'))
        evidence=claim.get('evidence')
        if not isinstance(evidence,list) or status=='supported' and not evidence:
            failures.append(issue('evidence_missing',cid,'Evidence list required, nonempty for supported claim'))
            continue
        for e in evidence:
            if not isinstance(e,dict) or not nonempty(e.get('block_id')) or not nonempty(e.get('quote')) or e.get('support') not in ('direct','indirect'):
                failures.append(issue('evidence_schema',cid,'Evidence needs block_id, exact quote and support classification'))
                continue
            if e['block_id'] not in bi:
                failures.append(issue('evidence_anchor',cid,'Evidence block does not resolve',block_id=e['block_id']))
            elif isinstance(bi[e['block_id']].get('text'),str) and normalized(e['quote']) not in normalized(bi[e['block_id']]['text']):
                failures.append(issue('quote_mismatch',cid,'Quote absent from cited block',block_id=e['block_id']))
    if failures:
        return report
    signatures={}
    for claim in claims:
        cid=claim['id']
        support=' '.join(e['quote'] for e in claim['evidence'])
        missing=sorted(numbers(claim['text'])-numbers(support))
        if missing:
            reviews.append(issue('numeric_support',cid,'Numeric tokens absent from attached quotes; review actual values/derivation',tokens=missing))
        if re.search(r'\b(?:and|whereas|therefore|because)\b|并且|而且|因此',claim['text'],re.I):
            reviews.append(issue('atomicity',cid,'Potential compound/causal construction; apply semantic atomicity test'))
        if not claim['conditions']:
            reviews.append(issue('scope',cid,'Check and record necessary conditions or explicit not-reported/not-applicable reason'))
        negative=bool(re.search(r'\b(?:not|no|neither|without|cannot)\b|不|未|无',claim['text'],re.I))
        if negative and claim['polarity']=='affirmed' or not negative and claim['polarity']=='negated':
            reviews.append(issue('polarity_scope',cid,'Text markers and polarity need a scope check; this heuristic does not resolve double negation'))
        if claim['origin']!='reported' or any(e['support']=='indirect' for e in claim['evidence']):
            reviews.append(issue('entailment',cid,'Interpretation/indirect evidence requires explicit premises and reasoning review'))
        if claim['relation']=='related_to' or claim['confidence']['level'] in ('low','undetermined'):
            reviews.append(issue('confidence_relation',cid,'Review weak confidence or fallback relation'))
        if any(bi[e['block_id']]['document_id']!=claim['document_id'] for e in claim['evidence']):
            reviews.append(issue('cross_source',cid,'Evidence belongs to another source: verify primary assertion attribution'))
        sig=canonical({key:claim[key] for key in ('document_id','subject','relation','object','polarity','modality','conditions')})
        if sig in signatures:
            reviews.append(issue('duplicate_scope',cid,'Same scoped content appears elsewhere; merge only if semantically equivalent',other_id=signatures[sig]))
        else:
            signatures[sig]=cid
    report['counts']={'documents':len(docs),'blocks':len(blocks),'claims':len(claims),
                      'supported':sum(c['status']=='supported' for c in claims),'excluded':len(pending)}
    report['status']='partial' if pending or not claims else 'review_required' if reviews else 'mechanical_pass'
    return report


def rdf_modules():
    try:
        import rdflib
        from rdflib import Dataset,Literal,Namespace,URIRef
        from rdflib.namespace import RDF,RDFS,XSD,DCTERMS,PROV
        return rdflib,Dataset,Literal,Namespace,URIRef,RDF,RDFS,XSD,DCTERMS,PROV
    except ImportError as exc:
        raise ValueError('RDFLib 7.x is required for RDF export/validation; checked JSON can still be delivered') from exc


def validate_dataset(dataset):
    _,_,_,Namespace,URIRef,RDF,_,_,_,_=rdf_modules()
    np=Namespace(NP_NS)
    heads=list(dataset.quads((None,RDF.type,np.Nanopublication,None)))
    errors=[]
    covered=set()
    roots=set()
    for root,_,_,head in heads:
        if root in roots:
            errors.append('Same nanopublication root is typed in more than one head')
        roots.add(root)
        links=[list(dataset.graph(head).objects(root,p)) for p in (np.hasAssertion,np.hasProvenance,np.hasPublicationInfo)]
        if any(len(v)!=1 for v in links):
            errors.append('Each head requires exactly one assertion/provenance/publication-info link')
            continue
        a,p,i=[v[0] for v in links]
        names={head,a,p,i}
        if len(names)!=4 or root in names or any(not isinstance(x,URIRef) for x in [root,*names]):
            errors.append('Nanopublication and its four graph identifiers must be distinct IRIs')
        if covered & names:
            errors.append('Two nanopublications share component graph identifiers')
        covered.update(names)
        if any(len(dataset.graph(g))==0 for g in names):
            errors.append('Nanopublication component graph is empty')
        if not any(s==a or o==a for s,_,o in dataset.graph(p)):
            errors.append('Provenance does not refer to assertion graph')
        if not any(s==root or o==root for s,_,o in dataset.graph(i)):
            errors.append('Publication info does not refer to nanopublication')
    active={g.identifier for g in dataset.graphs() if len(g)}
    if not heads:
        errors.append('No nanopublication head found')
    if active!=covered:
        errors.append('Triples occur outside the declared component graphs')
    return {'status':'pass' if not errors else 'fail','nanopublications':len(heads),
            'nonempty_graphs':len(active),'failures':errors,
            'scope':'Basic four-graph guideline invariants only; no signature, Trusty URI or semantic validation'}


def quad_set(dataset):
    return set(dataset.quads((None,None,None,None)))


def export(data,prefix):
    qa=audit(data)
    if qa['failures']:
        raise ValueError('Invalid claim ledger: '+canonical(qa['failures']))
    rdflib,Dataset,Literal,Namespace,URIRef,RDF,RDFS,XSD,DCT,PROV=rdf_modules()
    dataset=Dataset()
    np,V=Namespace(NP_NS),Namespace(VOCAB_NS)
    relation_config=read(RELATION_FILE)
    di={d['id']:d for d in data['documents']}
    bi={b['id']:b for b in data['blocks']}
    manifest={'case_id':data['case_id'],'status':'local_unsigned_drafts','trusty_uri':False,'published':False,
              'rdflib':rdflib.__version__,'included':[],'excluded':qa['excluded_candidates']}
    lines=['# Nanopublication review','',f'Case: {data["case_id"]}',
           '', 'Local unsigned drafts; no public publication, signatures or Trusty URIs.', '']
    for claim in data['claims']:
        if claim['status']!='supported':
            continue
        provenance=[{'evidence':e,'block':bi[e['block_id']],'document':di[bi[e['block_id']]['document_id']]} for e in claim['evidence']]
        identity=canonical({'case_id':data['case_id'],'claim':claim,'source':di[claim['document_id']],
                            'provenance':provenance,'publication':data['publication']})
        root=URIRef('urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,identity)))
        H,A,P,I=[URIRef(str(root)+'#'+suffix) for suffix in ('head','assertion','provenance','pubinfo')]
        head,assertion,prov,info=[dataset.graph(g) for g in (H,A,P,I)]
        head.add((root,RDF.type,np.Nanopublication))
        for predicate,graph in ((np.hasAssertion,A),(np.hasProvenance,P),(np.hasPublicationInfo,I)):
            head.add((root,predicate,graph))
        statement=URIRef(str(root)+'#claim')
        subject=URIRef(claim['subject'].get('iri') or str(root)+'#subject')
        obj=URIRef(claim['object']['iri']) if claim['object'].get('iri') else Literal(claim['object']['label'])
        predicate=URIRef(relation_config['namespace']+claim['relation'])
        # Reification retains the claim without entailing an unconditional S-P-O triple.
        assertion.add((statement,RDF.type,RDF.Statement))
        assertion.add((statement,RDF.type,V.ScopedAssertion))
        assertion.add((statement,RDF.subject,subject))
        assertion.add((subject,RDFS.label,Literal(claim['subject']['label'])))
        assertion.add((statement,RDF.predicate,predicate))
        assertion.add((predicate,RDFS.comment,Literal(relation_config['relations'][claim['relation']])))
        assertion.add((statement,RDF.object,obj))
        if claim['object'].get('iri'):
            assertion.add((obj,RDFS.label,Literal(claim['object']['label'])))
        assertion.add((statement,RDF.value,Literal(claim['text'])))
        for field in ('polarity','modality','origin'):
            assertion.add((statement,V[field],Literal(claim[field])))
        for condition in claim['conditions']:
            assertion.add((statement,V.condition,Literal(condition)))
        assertion.add((statement,V.confidenceLevel,Literal(claim['confidence']['level'])))
        assertion.add((statement,V.confidenceBasis,Literal(claim['confidence']['basis'])))
        if claim.get('inference_basis'):
            assertion.add((statement,V.inferenceBasis,Literal(claim['inference_basis'])))
        extractor=URIRef(str(root)+'#extractor')
        info.add((root,DCT.creator,extractor))
        info.add((extractor,RDF.type,PROV.Agent))
        info.add((extractor,RDFS.label,Literal(data['publication']['creator'])))
        info.add((root,DCT.created,Literal(data['publication']['created_at'],datatype=XSD.dateTime)))
        info.add((root,V.identifierStatus,Literal('local unsigned draft; not a Trusty URI')))
        info.add((root,RDFS.label,Literal(claim['text'])))
        if claim['origin']=='inference':
            prov.add((A,PROV.wasAttributedTo,extractor))
        primary=di[claim['document_id']]
        primary_uri=URIRef('urn:litnp:source:'+primary['sha256'].lower())
        prov.add((A,V.primarySource,primary_uri))
        prov.add((primary_uri,V.sourceMetadata,Literal(canonical(primary))))
        for index,entry in enumerate(provenance):
            e,b,d=entry['evidence'],entry['block'],entry['document']
            ev=URIRef(str(root)+'#evidence-'+str(index))
            doc=URIRef('urn:litnp:source:'+d['sha256'].lower())
            prov.add((A,PROV.wasDerivedFrom,ev))
            prov.add((ev,PROV.wasQuotedFrom,doc))
            prov.add((ev,RDF.value,Literal(e['quote'])))
            prov.add((ev,V.locator,Literal(canonical(b['locator']))))
            prov.add((ev,V.blockId,Literal(b['id'])))
            prov.add((ev,V.support,Literal(e['support'])))
            prov.add((doc,DCT.title,Literal(d['title'])))
            prov.add((doc,V.sha256,Literal(d['sha256'].lower())))
            prov.add((doc,V.sourcePath,Literal(d['path'])))
            for field in ('year','version','identifier'):
                if d.get(field) is not None:
                    pred=DCT.issued if field=='year' else DCT.hasVersion if field=='version' else DCT.identifier
                    prov.add((doc,pred,Literal(d[field])))
            if d.get('metadata_missing'):
                prov.add((doc,V.missingMetadata,Literal(canonical(d['metadata_missing']))))
            for ai,author in enumerate(d['authors']):
                person=URIRef(str(doc)+'#author-'+str(ai))
                prov.add((doc,DCT.creator,person))
                prov.add((person,RDFS.label,Literal(author)))
                if claim['origin']!='inference' and d['id']==claim['document_id']:
                    prov.add((A,PROV.wasAttributedTo,person))
        manifest['included'].append({'claim_id':claim['id'],'uri':str(root),'graphs':[str(x) for x in (H,A,P,I)]})
        lines.extend(['## '+claim['id'],'',claim['text'],'',
                      'Scope: '+canonical({'polarity':claim['polarity'],'modality':claim['modality'],'conditions':claim['conditions']}),''])
        for entry in provenance:
            lines.extend(['Evidence: '+entry['evidence']['quote'],
                          'Source: '+entry['document']['title']+' / '+entry['block']['id']+' / '+canonical(entry['block']['locator']),''])
    if not manifest['included']:
        raise ValueError('No supported claims to export; retain partial JSON and unresolved candidates')
    verification=validate_dataset(dataset)
    if verification['failures']:
        raise ValueError(canonical(verification))
    prefix=Path(prefix)
    prefix.parent.mkdir(parents=True,exist_ok=True)
    trig=dataset.serialize(format='trig')
    jsonld=dataset.serialize(format='json-ld',indent=2)
    first,second=Dataset(),Dataset()
    first.parse(data=trig,format='trig')
    second.parse(data=jsonld,format='json-ld')
    if quad_set(first)!=quad_set(dataset) or quad_set(second)!=quad_set(dataset):
        raise ValueError('RDF round-trip changes actual quads')
    manifest['rdf_validation']=verification
    manifest['round_trip_quad_equality']=True
    for suffix,content in (('.trig',trig),('.jsonld',jsonld),('.md','\n'.join(lines)),('.manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))):
        Path(str(prefix)+suffix).write_text(content,encoding='utf-8')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('check','export','validate-rdf'))
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    try:
        if args.command=='export':
            result=export(read(args.input),args.out)
        else:
            if args.command=='check':
                result=audit(read(args.input))
            else:
                _,Dataset,*_=rdf_modules()
                dataset=Dataset()
                dataset.parse(str(args.input),format='trig')
                result=validate_dataset(dataset)
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'command':args.command,'status':result['status'],'out':str(args.out)},ensure_ascii=False))
        return 1 if result.get('failures') or result.get('status')=='partial' else 0
    except Exception as exc:
        error={'status':'failed','error':f'{type(exc).__name__}: {exc}'}
        if args.command!='export':
            try:
                args.out.parent.mkdir(parents=True,exist_ok=True)
                args.out.write_text(json.dumps(error,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError:
                pass
        print(json.dumps(error,ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
