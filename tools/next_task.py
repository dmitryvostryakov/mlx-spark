import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--agent',choices=['Sol','Terra','Luna','any'],default='any');a=p.parse_args()
tasks=json.loads((ROOT/'planning/tasks.json').read_text())['tasks'];done={t['id'] for t in tasks if t['status']=='done'}
ready=[t for t in tasks if t['phase']=='single_spark' and t['status'] in {'todo','ready'} and set(t['depends_on'])<=done and (a.agent=='any' or t['owner']==a.agent)]
print(json.dumps({'ready':[{'id':t['id'],'title':t['title'],'read':f"planning/tasks/{t['id']}.md"} for t in ready],
 'note':'No task is claimed or executed by this read-only command. Follow handoff/AGENT_PROTOCOL.md.'},ensure_ascii=False,indent=2))
