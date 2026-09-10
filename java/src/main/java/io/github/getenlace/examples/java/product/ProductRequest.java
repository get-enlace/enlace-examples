package io.github.getenlace.examples.java.product;

import java.math.BigDecimal;

record ProductRequest(String name, BigDecimal price, int stock) {
}
