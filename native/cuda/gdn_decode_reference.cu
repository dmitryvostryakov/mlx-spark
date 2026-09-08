#include "mlx_spark/gdn_reference.cuh"
#include <cstdint>
#include <climits>
// One block per (batch, value head, value row). Simple baseline, not an optimized kernel.
__global__ void step(const float* q,const float* k,const float* v,const float* g,
    const float* beta,const float* state,const unsigned char* mask,float* y,float* out,
    int Hk,int Hv,int Dk,int Dv) {
  const int d=threadIdx.x;
  const std::int64_t row=blockIdx.x;
  const int dv=row%Dv;
  const int hv=(row/Dv)%Hv;
  const int b=row/(static_cast<std::int64_t>(Hv)*Dv);
  const int hk=hv/(Hv/Hk);
  const std::int64_t si=row*Dk+d;
  const std::int64_t qi=(static_cast<std::int64_t>(b)*Hk+hk)*Dk+d;
  const std::int64_t gi=static_cast<std::int64_t>(b)*Hv+hv;
  if (mask && !mask[b]) { out[si]=state[si]; if(d==0)y[row]=0.0f; return; }
  extern __shared__ float tmp[];
  float s=state[si]*g[gi];
  tmp[d]=s*k[qi]; __syncthreads();
  for(int offset=Dk/2;offset>0;offset/=2){if(d<offset)tmp[d]+=tmp[d+offset];__syncthreads();}
  const float delta=(v[row]-tmp[0])*beta[gi];
  // Ensure every thread has read tmp[0] before overwriting shared reduction storage.
  __syncthreads();
  s += delta*k[qi]; out[si]=s;
  tmp[d]=s*q[qi]; __syncthreads();
  for(int offset=Dk/2;offset>0;offset/=2){if(d<offset)tmp[d]+=tmp[d+offset];__syncthreads();}
  if(d==0)y[row]=tmp[0];
}
cudaError_t launch_gdn_decode_reference(const float* q,const float* k,const float* v,
    const float* g,const float* beta,const float* state,const unsigned char* mask,
    float* y,float* next_state,int B,int Hk,int Hv,int Dk,int Dv,cudaStream_t stream){
  if(!q||!k||!v||!g||!beta||!state||!y||!next_state||B<=0||Hk<=0||Hv<=0||Dv<=0||Hv%Hk)
    return cudaErrorInvalidValue;
  if(Dk!=32&&Dk!=64&&Dk!=128&&Dk!=256)return cudaErrorInvalidValue;
  if(next_state==state||y==v||next_state==y)return cudaErrorInvalidValue;
  // Bound sizes for the limited reference implementation; no dimension overflow.
  if(B>65535||Hv>65535||Dv>65535)return cudaErrorInvalidValue;
  const std::int64_t rows=static_cast<std::int64_t>(B)*Hv*Dv;
  if(rows>INT_MAX)return cudaErrorInvalidValue;
  step<<<static_cast<unsigned>(rows),Dk,Dk*sizeof(float),stream>>>(q,k,v,g,beta,state,mask,y,next_state,Hk,Hv,Dk,Dv);
  return cudaGetLastError();
}
