package io.github.getenlace.examples.java.customer;

import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * In-memory only, per running instance — resets on restart (see CONTRACT.md). Public: the
 * order package calls {@link #exists(int)} to validate a referenced {@code customerId}.
 */
@Component
public class CustomerStore {

    private final Map<Integer, Customer> customers = new ConcurrentHashMap<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    Collection<Customer> list() {
        return customers.values();
    }

    Customer get(int id) {
        return customers.get(id);
    }

    public boolean exists(int id) {
        return customers.containsKey(id);
    }

    Customer save(Customer customer) {
        customers.put(customer.id(), customer);
        return customer;
    }

    int nextId() {
        return nextId.getAndIncrement();
    }

    boolean delete(int id) {
        return customers.remove(id) != null;
    }
}
