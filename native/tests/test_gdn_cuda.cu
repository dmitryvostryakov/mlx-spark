#include "mlx_spark/gdn_reference.cuh"
#include <vector>
#include <cmath>
#include <iostream>
#include <stdexcept>
static void ok(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
template<class T> struct Buffer{
 T* p=nullptr;
 explicit Buffer(std::size_t n){ok(cudaMalloc(reinterpret_cast<void**>(&p),n*sizeof(T)));}
 ~Buffer(){if(p)cudaFree(p);}
 Buffer(const Buffer&)=delete;Buffer& operator=(const Buffer&)=delete;
};
int main(){
 int n=0;if(cudaGetDeviceCount(&n)!=cudaSuccess||n!=1){std::cerr<<"NEEDS_REAL_SINGLE_GPU\n";return 77;}
 try{
  const int B=2,Hk=2,Hv=4,Dk=128,Dv=5;
  std::vector<float> q(B*Hk*Dk),k(q.size()),v(B*Hv*Dv),g(B*Hv,.91f),beta(B*Hv,.31f),s(B*Hv*Dv*Dk);
  for(std::size_t i=0;i<q.size();++i){q[i]=.003f*int(i%13);k[i]=.002f*int(i%7);}
  for(std::size_t i=0;i<v.size();++i)v[i]=.01f*int(i%9);
  for(std::size_t i=0;i<s.size();++i)s[i]=.001f*int(i%17);
  std::vector<unsigned char> mask{1,0};
  auto cpu_s=s;std::vector<float> cpu_y(v.size(),0),got_y(v.size()),got_s(s.size());
  for(int b=0;b<B;++b)for(int h=0;h<Hv;++h)for(int dv=0;dv<Dv;++dv){
   const int row=(b*Hv+h)*Dv+dv;if(!mask[b])continue;
   const int hq=h/(Hv/Hk);float r=0;
   for(int d=0;d<Dk;++d){cpu_s[row*Dk+d]*=g[b*Hv+h];r+=cpu_s[row*Dk+d]*k[(b*Hk+hq)*Dk+d];}
   const float delta=beta[b*Hv+h]*(v[row]-r);
   for(int d=0;d<Dk;++d){cpu_s[row*Dk+d]+=delta*k[(b*Hk+hq)*Dk+d];cpu_y[row]+=cpu_s[row*Dk+d]*q[(b*Hk+hq)*Dk+d];}
  }
  Buffer<float> dq(q.size()),dk(k.size()),dv(v.size()),dg(g.size()),db(beta.size()),ds(s.size()),dy(v.size()),out(s.size());
  Buffer<unsigned char> dm(mask.size());
  auto copy=[](float* dst,const std::vector<float>& src){ok(cudaMemcpy(dst,src.data(),src.size()*sizeof(float),cudaMemcpyHostToDevice));};
  copy(dq.p,q);copy(dk.p,k);copy(dv.p,v);copy(dg.p,g);copy(db.p,beta);copy(ds.p,s);
  ok(cudaMemcpy(dm.p,mask.data(),mask.size(),cudaMemcpyHostToDevice));
  ok(launch_gdn_decode_reference(dq.p,dk.p,dv.p,dg.p,db.p,ds.p,dm.p,dy.p,out.p,B,Hk,Hv,Dk,Dv,nullptr));
  ok(cudaDeviceSynchronize());
  ok(cudaMemcpy(got_y.data(),dy.p,got_y.size()*sizeof(float),cudaMemcpyDeviceToHost));
  ok(cudaMemcpy(got_s.data(),out.p,got_s.size()*sizeof(float),cudaMemcpyDeviceToHost));
  for(std::size_t i=0;i<got_y.size();++i)if(!std::isfinite(got_y[i])||std::abs(got_y[i]-cpu_y[i])>5e-4f)return 2;
  for(std::size_t i=0;i<got_s.size();++i)if(!std::isfinite(got_s[i])||std::abs(got_s[i]-cpu_s[i])>5e-4f)return 3;
  std::cout<<"One FP32 toy case passed. Not Qwen/precision/training validation.\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
