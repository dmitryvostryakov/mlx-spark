"""Small dense GQA attention oracle. Never use for a full 32K prefill."""
import numpy as np
from ..errors import ContractError

def causal_gqa(q,k,v, *, scale=None):
    q,k,v=[np.asarray(x,dtype=np.float64) for x in (q,k,v)]
    if q.ndim!=4 or k.ndim!=4 or v.shape!=k.shape or q.shape[0]!=k.shape[0] or q.shape[-1]!=k.shape[-1]:
        raise ContractError("Expected B,T,H,D tensors with matching head dims")
    B,T,H,D=q.shape; S,Hkv=k.shape[1:3]
    if Hkv<=0 or H%Hkv or T<=0 or S<T: raise ContractError("Invalid GQA dimensions")
    kr=np.repeat(k,H//Hkv,axis=2);vr=np.repeat(v,H//Hkv,axis=2)
    scores=np.einsum('bthd,bshd->bhts',q,kr)*(D**-0.5 if scale is None else scale)
    allowed=np.arange(S)[None,:]<=np.arange(S-T,S)[:,None]
    scores=np.where(allowed[None,None],scores,-np.inf)
    p=np.exp(scores-np.max(scores,axis=-1,keepdims=True));p/=p.sum(axis=-1,keepdims=True)
    return np.einsum('bhts,bshd->bthd',p,vr)

def rms_norm(x,weight,eps=1e-6, *, unit_offset=False):
    x=np.asarray(x,dtype=np.float64);w=np.asarray(weight,dtype=np.float64)
    return x/np.sqrt(np.mean(x*x,axis=-1,keepdims=True)+eps)*(w+1 if unit_offset else w)
