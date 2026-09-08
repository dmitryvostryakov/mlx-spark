#include "mlx_spark/contracts.hpp"
#include <array>
#include <iostream>
#include <limits>
int main() {
  using mlx_spark::checked_product;
  if (checked_product(std::array<std::uint64_t,3>{2,3,4}) != 24) return 1;
  if (checked_product(std::array<std::uint64_t,0>{}) != 1) return 2;
  if (checked_product(std::array<std::uint64_t,3>{0,~0ULL,~0ULL}) != 0) return 3;
  try { checked_product(std::array<std::uint64_t,2>{~0ULL,2}); return 4; }
  catch (const std::overflow_error&) {}
  mlx_spark::PrimitiveContract c;
  if (c.forward || c.hardware_validated || c.vjp) return 5;
  std::cout << "host contract tests passed; no GPU was tested\n";
}
