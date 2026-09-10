package io.github.getenlace.examples.java.order;

import java.math.BigDecimal;

record OrderItem(int productId, int quantity, BigDecimal unitPrice) {
}
