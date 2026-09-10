package io.github.getenlace.examples.java.order;

import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * In-memory only, per running instance — resets on restart (see CONTRACT.md). Package-private:
 * unlike {@code customer.CustomerStore}/{@code product.ProductStore}, nothing outside this
 * package needs an order's existence checked or its price looked up.
 */
@Component
class OrderStore {

    private final Map<Integer, Order> orders = new ConcurrentHashMap<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    Collection<Order> list() {
        return orders.values();
    }

    Order get(int id) {
        return orders.get(id);
    }

    Order save(Order order) {
        orders.put(order.id(), order);
        return order;
    }

    int nextId() {
        return nextId.getAndIncrement();
    }

    boolean delete(int id) {
        return orders.remove(id) != null;
    }
}
