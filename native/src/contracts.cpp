#include "mlx_spark/contracts.hpp"
#include <limits>
namespace mlx_spark {
std::uint64_t checked_product(std::span<const std::uint64_t> dimensions) {
  // Empty dimension list is a scalar. Any zero dimension means an empty array.
  for (auto n : dimensions) if (n == 0) return 0;
  std::uint64_t product = 1;
  for (auto n : dimensions) {
    if (product > std::numeric_limits<std::uint64_t>::max() / n)
      throw std::overflow_error("tensor element count overflow");
    product *= n;
  }
  return product;
}
}
