import numpy as np
import pytest
from mlx_spark.reference.attention import causal_gqa,rms_norm
from mlx_spark.reference.state import ReferenceSnapshot
from mlx_spark.reference.training import analytic_sgd,save_reference,load_reference
pytestmark=pytest.mark.reference

def test_attention_whole_vs_cached():
 r=np.random.default_rng(9);q=r.normal(size=(2,5,4,3));k=r.normal(size=(2,5,2,3));v=r.normal(size=k.shape)
 y=causal_gqa(q,k,v)
 pieces=[causal_gqa(q[:,i:i+1],k[:,:i+1],v[:,:i+1]) for i in range(5)]
 np.testing.assert_allclose(y,np.concatenate(pieces,1),rtol=1e-12,atol=1e-12)

def test_unit_offset_is_explicit():
 x=np.ones((2,3));w=np.zeros(3)
 np.testing.assert_array_equal(rms_norm(x,w),0)
 assert np.all(rms_norm(x,w,unit_offset=True)>.99)

def test_snapshot_is_deep_copy():
 x=np.ones((2,3));s=ReferenceSnapshot(5,x,x);child=s.fork();x[:]=99
 assert np.all(s.recurrent==1) and not np.shares_memory(s.recurrent,child.recurrent)
 with pytest.raises(ValueError):s.recurrent[0,0]=0

def test_analytic_reference_resume(tmp_path):
 r=np.random.default_rng(5);x=r.normal(size=(32,3));target=r.normal(size=(3,2));y=x@target
 w=np.zeros((3,2));initial=np.mean((x@w-y)**2)
 full=w.copy()
 for _ in range(60):full=analytic_sgd(full,x,y,.1)
 for _ in range(30):w=analytic_sgd(w,x,y,.1)
 p=tmp_path/'ref.json';save_reference(p,w,30);w,step=load_reference(p);assert step==30
 for _ in range(30):w=analytic_sgd(w,x,y,.1)
 np.testing.assert_array_equal(w,full)
 assert np.mean((x@w-y)**2)<initial*.02
