import json
from om_ai.data.governance import CorpusGovernance
from om_ai.continuous import FeedbackStore, build_sft_replay, build_preference_replay
from om_ai.integrations import PluginRegistry, IntegrationPlugin, ActionSpec

class Dummy(IntegrationPlugin):
    def health(self): return {'ok':True}
    def actions(self): return [ActionSpec('ping','ping',{},False)]
    def execute(self,action,arguments): return 'pong'

def test_governance_rejects_unlicensed(tmp_path):
    p=tmp_path/'m.json'; p.write_text(json.dumps({'sources':[{'source_id':'x','uri':'x','license':'unknown','owner':'me','allowed_for_training':True}]}))
    try: CorpusGovernance.load_manifest(p)
    except ValueError: pass
    else: raise AssertionError('unknown license must be rejected')

def test_feedback_replay_and_plugin(tmp_path):
    store=FeedbackStore(str(tmp_path/'f.db')); store.add('p','bad',1,preferred_response='good'); store.add('p2','great',5)
    assert build_sft_replay(store,tmp_path/'sft.jsonl',4)==1
    assert build_preference_replay(store,tmp_path/'pref.jsonl')==1
    reg=PluginRegistry(); reg.register('d',Dummy()); assert reg.get('d').execute('ping',{})=='pong'; assert reg.discover()['d'][0]['name']=='ping'
