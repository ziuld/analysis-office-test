"""Discovery maps must not preload reports; retrieval stays local and review-scoped."""
import json
import tempfile
import unittest
from pathlib import Path
from arktic_office.storage.knowledge import Knowledge
from arktic_office.preparation.evidence import Evidence
from arktic_office.reporting.deterministic import context
from arktic_office.coordination.research import research
from test_questionnaire import fixture


class LookupMapTests(unittest.TestCase):
    def store(self, root):
        store=Knowledge(root)
        snapshot,_=fixture()
        answer={'id':'Q04','estado':'parcial','respuesta':'Respuesta original TEST_ANSWER_PAYLOAD',
                'pendiente':'Sin alterar','evidencia':[{'path':'app.py','line':n,'quote':'TEST_QUOTE_PAYLOAD'} for n in range(1,201)]}
        for run,text in [('a',answer['respuesta']),('b','OTHER_REVISION_PAYLOAD')]:
            store.begin(run,snapshot)
            store.task(run,{'id':'inventory'}, {'estado':'completada'}, {'respuestas':[{**answer,'respuesta':text,'author':'declared-by-model'}]})
        return store,answer

    def test_map_has_question_and_author_without_answer_or_quotes(self):
        with tempfile.TemporaryDirectory() as root:
            store,_=self.store(root)
            index=store.index('a')
            self.assertEqual([q['id'] for q in index],['Q04'])
            self.assertEqual(index[0]['author'],'inventory')
            self.assertNotIn('PAYLOAD',json.dumps(index))
            self.assertNotIn('respuesta',index[0])

    def test_answer_lookup_preserves_text_and_compacts_sources_without_other_revision(self):
        with tempfile.TemporaryDirectory() as root:
            store,answer=self.store(root)
            e=Evidence([],{'nodes':[],'edges':[]});e.knowledge=store;e.run_id='a'
            found=e.lookup({'questions':['Q04']})['answers'][0]
            self.assertEqual(found['answer']['respuesta'],answer['respuesta'])
            self.assertEqual(found['answer']['estado'],answer['estado'])
            self.assertEqual(found['answer']['author'],'inventory')
            self.assertEqual(found['sources'],[{'path':'app.py','start_line':1,'end_line':200}])
            self.assertNotIn('TEST_QUOTE_PAYLOAD',json.dumps(found))
            self.assertNotIn('OTHER_REVISION_PAYLOAD',json.dumps(found))
            mixed=e.lookup({'questions':['Q04','Q05']})
            self.assertEqual(len(mixed['answers']),1)
            self.assertEqual(mixed['unavailable'],['Q05'])
            self.assertNotIn('error',mixed)
            for request in ({'questions':['Q05']},{'questions':['Q04'],'run':'b'},
                            {'questions':['Q04']*5},{'questions':['Q04'],'offset':-1},
                            {'questions':['Q04 OR 1=1']},{'questions':['Q04'],'tool':'D04'}):
                self.assertIn('error',e.respond(request))
            self.assertEqual(store.answer('a','Q04')['evidencia'],answer['evidencia'])

    def test_tool_map_excludes_results_and_scanner_detail(self):
        snapshot,e=fixture()
        snapshot['deterministic_results']['tools'][1]['detail']='PRIVATE_DETAIL_PAYLOAD'
        mapped=context(snapshot)
        encoded=json.dumps(mapped)
        self.assertNotIn('alert(1)',encoded)
        self.assertNotIn('PRIVATE_DETAIL_PAYLOAD',encoded)
        self.assertNotIn('findings"',encoded)
        self.assertEqual(mapped[1]['findings_total'],1)

    def test_scanner_filters_index_and_pagination_do_not_read_other_findings(self):
        _,e=fixture()
        e.deterministic['tools'][3]['result']['findings']=[
            {'path':'page.js','line':i+1,'summary':'xss rule' if i%2==0 else 'other rule','extra':'DETAIL_'+str(i)} for i in range(45)]
        request={'tool':'D04','paths':['page.js'],'query':'xss','limit':2}
        index=e.lookup({**request,'index':True})
        self.assertEqual(index['total'],23)
        self.assertEqual(index['next_offset'],2)
        self.assertNotIn('extra',index['entries'][0])
        detail=e.lookup({**request,'offset':2})
        self.assertEqual([x['extra'] for x in detail['findings']],['DETAIL_4','DETAIL_6'])
        self.assertEqual(e.lookup({'tool':'D04','paths':['other.js']})['findings'],[])
        self.assertIn('error',e.respond({**request,'limit':21}))

    def test_oversized_tool_element_never_returns_a_nonadvancing_page(self):
        _,e=fixture()
        e.deterministic['tools'][1]['result']['findings']=[{'path':'app.py','summary':'x'*13000}]
        result=e.respond({'tool':'D02'})
        self.assertIn('error',result)
        self.assertNotIn('next_offset',result)

    def test_sql_scanner_graph_and_source_queries_share_one_round(self):
        with tempfile.TemporaryDirectory() as root:
            store,answer=self.store(root)
            snapshot,e=fixture();e.knowledge=store;e.run_id='a'
            e.graph={'nodes':[{'id':'entry','label':'main','source_file':'app.py','source_location':'L1'}],'edges':[]}
            config={'id':'inventory','name':'Inventario','focus':'Revisar','files':[],
                    'knowledge_index':store.index('a'),'limits':{'research_rounds':1,'files':10,'bytes':12000}}
            prompts=[]
            def invoke(prompt,config):
                prompts.append(prompt)
                if len(prompts)==1:
                    self.assertNotIn('TEST_ANSWER_PAYLOAD',prompt)
                    self.assertNotIn('alert(1)',prompt)
                    self.assertEqual(prompt.count('Posibles credenciales: Gitleaks'),1)
                    return {'report':json.dumps({'queries':[{'questions':['Q04']},{'tool':'D02','limit':1},{'query':'main'}]})}
                self.assertIn(answer['respuesta'],prompt)
                self.assertIn('alert(1)',prompt)
                self.assertIn("print('hello')",prompt)
                self.assertNotIn('TEST_QUOTE_PAYLOAD',prompt)
                return {'report':json.dumps({'observaciones':[],'respuestas':[]})}
            state={}
            research(snapshot,config,state,e,invoke,Path(root),[])
            self.assertEqual(len(prompts),2)
            self.assertEqual(len(state['retrievals']),3)
            self.assertEqual(state['archivos'],['app.py'])
            self.assertIn('context_sections',state['invocations'][0])
