#include <cuda_runtime.h>
#include <iostream>
int main(){
  int count=0;auto err=cudaGetDeviceCount(&count);
  if(err!=cudaSuccess){std::cerr<<cudaGetErrorString(err)<<"\n";return 2;}
  if(count!=1){std::cerr<<"Select exactly one visible GPU for phase 1; found "<<count<<"\n";return 3;}
  cudaDeviceProp p{};if(cudaGetDeviceProperties(&p,0)!=cudaSuccess)return 4;
  int driver=0,runtime=0;cudaDriverGetVersion(&driver);cudaRuntimeGetVersion(&runtime);
  std::cout<<"{\"kind\":\"cuda_capability_probe_only\",\"compute_major\":"<<p.major
    <<",\"compute_minor\":"<<p.minor<<",\"driver_api_version\":"<<driver
    <<",\"runtime_api_version\":"<<runtime<<",\"unified_addressing\":"<<p.unifiedAddressing
    <<",\"managed_memory\":"<<p.managedMemory<<",\"concurrent_managed_access\":"<<p.concurrentManagedAccess
    <<",\"pageable_memory_access\":"<<p.pageableMemoryAccess<<",\"reported_global_bytes\":"<<p.totalGlobalMem<<"}\n";
  return (p.major==12&&p.minor==1)?0:5;
}
