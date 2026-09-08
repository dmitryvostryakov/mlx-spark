import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tasks=json.loads((ROOT/'planning/tasks.json').read_text())['tasks'];by={t['id']:t for t in tasks}
if len(by)!=len(tasks):raise SystemExit('duplicate task IDs')
seen=set();active=set()
def visit(i):
 if i in active:raise ValueError('dependency cycle at '+i)
 if i in seen:return
 active.add(i)
 for d in by[i]['depends_on']:
  if d not in by:raise ValueError('missing dependency '+d)
  if by[i]['phase']=='single_spark' and by[d]['phase']!='single_spark':raise ValueError('phase 1 depends on deferred work')
  visit(d)
 active.remove(i);seen.add(i)
for i,t in by.items():
 visit(i)
 if not (ROOT/f'planning/tasks/{i}.md').is_file():raise ValueError('missing task card '+i)
 if t['owner'] not in {'Sol','Terra','Luna'}:raise ValueError('unknown owner')
print(json.dumps({'tasks':len(tasks),'acyclic':True,'single_spark':sum(t['phase']=='single_spark' for t in tasks),'deferred':sum(t['phase']!='single_spark' for t in tasks)}))
