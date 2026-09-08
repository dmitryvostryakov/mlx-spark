from _bootstrap import ROOT
from mlx_spark.benchmark import TimingSeries,validate_comparison
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description='Summarize already measured data; does NOT benchmark a model')
p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args()
x=json.loads(a.baseline.read_text());y=json.loads(a.candidate.read_text());validate_comparison(x,y)
sx=TimingSeries(tuple(x['seconds']),x['generated_tokens']).summary()
sy=TimingSeries(tuple(y['seconds']),y['generated_tokens']).summary()
print(json.dumps({'baseline':sx,'candidate':sy,'median_time_ratio':sx['median_seconds']/sy['median_seconds'],
 'warning':'Results depend on truthful measured inputs. Ratio is descriptive, not a statistical significance test.'},indent=2))
