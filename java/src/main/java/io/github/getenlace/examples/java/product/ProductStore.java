package io.github.getenlace.examples.java.product;

import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * In-memory only, per running instance — resets on restart (see CONTRACT.md). Public: the
 * order package calls {@link #get(int)} to validate a referenced {@code productId} and to
 * read its current price when pricing a new order.
 */
@Component
public class ProductStore {

    private final Map<Integer, Product> products = new ConcurrentHashMap<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    Collection<Product> list() {
        return products.values();
    }

    public Product get(int id) {
        return products.get(id);
    }

    boolean exists(int id) {
        return products.containsKey(id);
    }

    Product save(Product product) {
        products.put(product.id(), product);
        return product;
    }

    int nextId() {
        return nextId.getAndIncrement();
    }

    boolean delete(int id) {
        return products.remove(id) != null;
    }
}
