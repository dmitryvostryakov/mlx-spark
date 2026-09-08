import argparse, json
from pathlib import Path
from .runtime.doctor import inventory
from .runtime.memory import estimate
from .models.qwen3_8.config import QwenTextSpec

def main(argv=None):
    p=argparse.ArgumentParser(description="MLX-Spark engineering scaffold; not yet an inference CLI")
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    sub.add_parser('doctor')
    m=sub.add_parser('memory-estimate')
    m.add_argument('--config',type=Path,required=True)
    m.add_argument('--tokens',type=int,required=True)
    m.add_argument('--batch',type=int,default=1)
    m.add_argument('--all-logits',action='store_true')
    m.add_argument('--nominal-parameters',type=int)
    m.add_argument('--weight-bits',type=int,default=16)
    a=p.parse_args(argv)
    if a.command=='status':
        out={"stage":"scaffold_only","native_core":False,"qwen_inference":False,
             "framework_training":False,"cuda_validated":False,"tp2":"deferred"}
    elif a.command=='doctor': out=inventory()
    else:
        spec=QwenTextSpec.from_mapping(json.loads(a.config.read_text()))
        out=estimate(spec,tokens=a.tokens,batch=a.batch,logits_positions=a.tokens if a.all_logits else 1,
                     nominal_parameters=a.nominal_parameters,weight_bits=a.weight_bits).to_dict()
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0
if __name__=='__main__': raise SystemExit(main())
