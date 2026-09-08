"""Analytic NumPy linear-regression fixture; deliberately NOT framework autograd."""
import json, os, tempfile
from pathlib import Path
import numpy as np

def analytic_sgd(w,x,y,lr):
    error=x@w-y
    return w-lr*(2/error.size)*(x.T@error)

def save_reference(path,w,step):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.checkpoint-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump({'schema':1,'kind':'analytic_numpy_reference','step':int(step),'weights':np.asarray(w).tolist()},f)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_reference(path):
    obj=json.loads(Path(path).read_text())
    if obj.get('schema')!=1 or obj.get('kind')!='analytic_numpy_reference':
        raise ValueError('Not a recognized reference checkpoint')
    return np.array(obj['weights'],dtype=np.float64),obj['step']
