import numpy as np
import pytest
from mlx_spark.reference.gdn import gdn_forward,gdn_vjp
from mlx_spark.errors import ContractError
pytestmark=pytest.mark.reference

def sample(B=2,T=5,Hk=2,Hv=4,Dk=3,Dv=2):
 r=np.random.default_rng(37)
 q=r.normal(size=(B,T,Hk,Dk))*.1;k=r.normal(size=q.shape)*.1
 v=r.normal(size=(B,T,Hv,Dv))*.2
 g=r.uniform(.8,.99,size=(B,T,Hv));beta=r.uniform(.1,.8,size=g.shape)
 s=r.normal(size=(B,Hv,Dv,Dk))*.1
 return q,k,v,g,beta,s

def test_chunk_equivalence():
 a=sample();whole,s=gdn_forward(*a)
 y1,s1=gdn_forward(*(x[:,:2] for x in a[:5]),a[5])
 y2,s2=gdn_forward(*(x[:,2:] for x in a[:5]),s1)
 np.testing.assert_array_equal(np.concatenate([y1,y2],axis=1),whole)
 np.testing.assert_array_equal(s2,s)

def test_mask_and_input_immutability():
 a=sample();saved=a[5].copy();mask=np.ones((2,5),bool);mask[0]=False
 y,s=gdn_forward(*a,mask=mask)
 np.testing.assert_array_equal(y[0],0);np.testing.assert_array_equal(s[0],saved[0])
 np.testing.assert_array_equal(a[5],saved)

def test_group_heads_match_repeat():
 a=sample();y,s=gdn_forward(*a)
 yr,sr=gdn_forward(np.repeat(a[0],2,2),np.repeat(a[1],2,2),*a[2:])
 np.testing.assert_array_equal(y,yr);np.testing.assert_array_equal(s,sr)

def test_zero_length():
 a=sample(T=0);y,s=gdn_forward(*a)
 assert y.shape==(2,0,4,2);np.testing.assert_array_equal(s,a[-1])

def test_bad_scalar_gate_shape():
 a=list(sample());a[3]=a[3][...,None]
 with pytest.raises(ContractError):gdn_forward(*a)

@pytest.mark.parametrize('use_mask',[False,True])
def test_vjp_against_finite_difference(use_mask):
 a=list(sample(B=1,T=3,Hk=1,Hv=2,Dk=2,Dv=2))
 r=np.random.default_rng(11);dy=r.normal(size=(1,3,2,2));ds=r.normal(size=a[-1].shape)
 mask=np.array([[True,False,True]]) if use_mask else None
 grads=gdn_vjp(*a,dy,ds,mask=mask)
 def objective(xs):
  y,s=gdn_forward(*xs,mask=mask);return float(np.sum(y*dy)+np.sum(s*ds))
 eps=1e-6
 for i,name in enumerate(('q','k','v','g','beta','state')):
  numerical=np.zeros_like(a[i])
  for idx in np.ndindex(a[i].shape):
   xp=[x.copy() for x in a];xm=[x.copy() for x in a]
   xp[i][idx]+=eps;xm[i][idx]-=eps
   numerical[idx]=(objective(xp)-objective(xm))/(2*eps)
  np.testing.assert_allclose(grads[name],numerical,rtol=2e-6,atol=2e-8,err_msg=name)

def test_masked_output_has_zero_gradient():
 a=sample();dy=np.ones((2,5,4,2));mask=np.zeros((2,5),bool)
 g=gdn_vjp(*a,dy,np.ones_like(a[-1]),mask=mask)
 for k in ('q','k','v','g','beta'):np.testing.assert_array_equal(g[k],0)
 np.testing.assert_array_equal(g['state'],1)
