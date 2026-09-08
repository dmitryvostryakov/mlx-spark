#pragma once
#include <cuda_runtime.h>
// ORIGINAL CORRECTNESS CANDIDATE, NOT COMPILED/VALIDATED IN THE HANDOFF ENVIRONMENT.
// Contiguous FP32 device pointers. q,k[B,Hk,Dk], v/y[B,Hv,Dv], g,beta[B,Hv],
// state[B,Hv,Dv,Dk]. mask is optional uint8[B]. q scaling is caller-owned.
// Every output allocation must be separate from every input; size/ownership are
// caller responsibilities. Limited reference shapes, not production dispatch.
cudaError_t launch_gdn_decode_reference(const float* q,const float* k,const float* v,
    const float* g,const float* beta,const float* state,const unsigned char* mask,
    float* y,float* next_state,int B,int Hk,int Hv,int Dk,int Dv,cudaStream_t stream);
