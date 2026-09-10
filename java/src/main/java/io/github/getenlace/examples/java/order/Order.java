package io.github.getenlace.examples.java.order;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

record Order(int id, int customerId, String status, List<OrderItem> items, BigDecimal total, Instant createdAt) {
}
