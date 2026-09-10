package io.github.getenlace.examples.java.product;

import java.math.BigDecimal;

/** Public: the order package reads {@link #price()} when pricing a new order's items. */
public record Product(int id, String name, BigDecimal price, int stock) {
}
