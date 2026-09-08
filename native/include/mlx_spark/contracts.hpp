#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
namespace mlx_spark {
// Small scaffold contract helpers; this is not an array or allocator implementation.
std::uint64_t checked_product(std::span<const std::uint64_t> dimensions);
struct PrimitiveContract {
  bool forward = false;
  bool vjp = false;
  bool jvp = false;
  bool vmap = false;
  bool higher_order = false;
  bool hardware_validated = false;
};
}
