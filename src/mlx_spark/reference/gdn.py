"""Original NumPy oracle for a scalar-gate, already-normalized GDN recurrence.

q,k: B,T,Hk,Dk. v: B,T,Hv,Dv. g,beta: B,T,Hv.
state: B,Hv,Dv,Dk. g is a multiplicative decay, NOT log-decay.
The caller owns q/k normalization and q readout scaling. No hidden Dk scale.
Masks are B,T bool: masked output is zero and state does not advance.
Float64 is a numerical oracle; it is not the target production precision.
"""
from dataclasses import dataclass
import numpy as np
from ..errors import ContractError

@dataclass
class _Step:
    prev: np.ndarray
    decayed: np.ndarray
    residual: np.ndarray
    delta: np.ndarray
    updated: np.ndarray

def _validate(q,k,v,g,beta,state,mask):
    q,k,v,g,beta=[np.asarray(x,dtype=np.float64) for x in (q,k,v,g,beta)]
    if q.ndim!=4 or k.shape!=q.shape or v.ndim!=4 or v.shape[:2]!=q.shape[:2]:
        raise ContractError("q/k must be B,T,Hk,Dk; v must be B,T,Hv,Dv")
    B,T,Hk,Dk=q.shape; Hv,Dv=v.shape[-2:]
    if min(B,Hk,Dk,Hv,Dv)<=0 or Hv%Hk:
        raise ContractError("Positive dimensions and integral Hv/Hk are required")
    if g.shape!=(B,T,Hv) or beta.shape!=g.shape:
        raise ContractError("This oracle supports scalar gates B,T,Hv only")
    state=np.zeros((B,Hv,Dv,Dk),np.float64) if state is None else np.asarray(state,dtype=np.float64)
    if state.shape!=(B,Hv,Dv,Dk): raise ContractError("Wrong state shape")
    mask=np.ones((B,T),bool) if mask is None else np.asarray(mask)
    if mask.shape!=(B,T) or mask.dtype!=np.bool_: raise ContractError("Mask must be B,T bool")
    if any(not np.isfinite(x).all() for x in (q,k,v,g,beta,state)):
        raise ContractError("Oracle inputs must be finite")
    return q,k,v,g,beta,state.copy(),mask

def _forward(q,k,v,g,beta,state=None,mask=None,record=False):
    q,k,v,g,beta,s,mask=_validate(q,k,v,g,beta,state,mask)
    B,T,Hk,Dk=q.shape; Hv,Dv=v.shape[-2:]; r=Hv//Hk
    qr=np.repeat(q,r,axis=2); kr=np.repeat(k,r,axis=2)
    y=np.zeros((B,T,Hv,Dv),np.float64); trace=[]
    for t in range(T):
        prev=s.copy(); decayed=prev*g[:,t,:,None,None]
        residual=v[:,t]-np.einsum('bhvk,bhk->bhv',decayed,kr[:,t])
        delta=beta[:,t,:,None]*residual
        updated=decayed+delta[...,None]*kr[:,t,:,None,:]
        active=mask[:,t,None,None,None]
        s=np.where(active,updated,prev)
        y[:,t]=np.where(mask[:,t,None,None],np.einsum('bhvk,bhk->bhv',updated,qr[:,t]),0)
        if record: trace.append(_Step(prev,decayed,residual,delta,updated))
    return y,s,(q,k,v,g,beta,mask,qr,kr,trace)

def gdn_forward(q,k,v,g,beta,state=None,mask=None):
    y,s,_=_forward(q,k,v,g,beta,state,mask)
    return y,s

def gdn_vjp(q,k,v,g,beta,state,dy,ds_final=None,mask=None):
    """Analytic first-order VJP oracle. Returns q,k,v,g,beta,state cotangents.

    This function is NOT a production autograd implementation.
    """
    y,s,cache=_forward(q,k,v,g,beta,state,mask,True)
    q,k,v,g,beta,mask,qr,kr,trace=cache
    dy=np.asarray(dy,dtype=np.float64)
    if dy.shape!=y.shape: raise ContractError("dy shape mismatch")
    carry=np.zeros_like(s) if ds_final is None else np.asarray(ds_final,dtype=np.float64).copy()
    if carry.shape!=s.shape: raise ContractError("final state cotangent shape mismatch")
    dqr=np.zeros_like(qr); dkr=np.zeros_like(kr); dv=np.zeros_like(v)
    dg=np.zeros_like(g); db=np.zeros_like(beta)
    for t in reversed(range(q.shape[1])):
        st=trace[t]; a=mask[:,t,None,None,None]
        yt=np.where(mask[:,t,None,None],dy[:,t],0)
        du=np.where(a,carry,0)+yt[...,None]*qr[:,t,:,None,:]
        dqr[:,t]=np.einsum('bhvk,bhv->bhk',st.updated,yt)
        dd=np.einsum('bhvk,bhk->bhv',du,kr[:,t])
        dkr[:,t]=np.einsum('bhvk,bhv->bhk',du,st.delta)
        db[:,t]=np.sum(dd*st.residual,axis=-1)
        dv[:,t]=dd*beta[:,t,:,None]
        dr=-dv[:,t]
        dp=du+dr[...,None]*kr[:,t,:,None,:]
        dkr[:,t]+=np.einsum('bhvk,bhv->bhk',st.decayed,dr)
        dg[:,t]=np.sum(dp*st.prev,axis=(-2,-1))
        carry=np.where(a,dp*g[:,t,:,None,None],carry)
    B,T,Hk,Dk=q.shape;r=v.shape[2]//Hk
    dq=dqr.reshape(B,T,Hk,r,Dk).sum(axis=3)
    dk=dkr.reshape(B,T,Hk,r,Dk).sum(axis=3)
    return {'q':dq,'k':dk,'v':dv,'g':dg,'beta':db,'state':carry}
