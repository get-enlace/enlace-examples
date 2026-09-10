package io.github.getenlace.examples.java.order;

import java.util.List;

record OrderRequest(int customerId, List<OrderItemRequest> items) {
}
