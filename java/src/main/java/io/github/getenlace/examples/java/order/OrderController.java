package io.github.getenlace.examples.java.order;

import io.github.getenlace.examples.java.common.ApiException;
import io.github.getenlace.examples.java.customer.CustomerStore;
import io.github.getenlace.examples.java.product.Product;
import io.github.getenlace.examples.java.product.ProductStore;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * References a Customer and one or more Products (see CONTRACT.md). {@code unitPrice} and
 * {@code total} are server-computed from each product's *current* price at creation time —
 * deliberately response-only fields the client didn't send, to give the canvas something
 * worth mapping from a response into a later step.
 */
// Without @Tag, springdoc falls back to a tag derived from the class name
// ("order-controller") — an implementation detail leaking into a user-facing grouping.
@Tag(name = "Orders")
@RestController
@RequestMapping("/orders")
class OrderController {

    private final OrderStore orders;
    private final CustomerStore customers;
    private final ProductStore products;

    OrderController(OrderStore orders, CustomerStore customers, ProductStore products) {
        this.orders = orders;
        this.customers = customers;
        this.products = products;
    }

    @GetMapping
    Collection<Order> listOrders() {
        return orders.list();
    }

    @GetMapping("/{id}")
    Order getOrder(@PathVariable int id) {
        Order order = orders.get(id);
        if (order == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Order " + id + " not found.");
        }
        return order;
    }

    @PostMapping
    ResponseEntity<Order> createOrder(@RequestBody OrderRequest request) {
        if (!customers.exists(request.customerId())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "customerId " + request.customerId() + " does not exist.");
        }

        List<OrderItem> items = new ArrayList<>();
        for (OrderItemRequest itemRequest : request.items()) {
            Product product = products.get(itemRequest.productId());
            if (product == null) {
                throw new ApiException(HttpStatus.BAD_REQUEST,
                        "productId " + itemRequest.productId() + " does not exist.");
            }
            items.add(new OrderItem(itemRequest.productId(), itemRequest.quantity(), product.price()));
        }

        BigDecimal total = items.stream()
                .map(item -> item.unitPrice().multiply(BigDecimal.valueOf(item.quantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        Order order = orders.save(
                new Order(orders.nextId(), request.customerId(), "pending", items, total, Instant.now()));
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @PutMapping("/{id}/status")
    Order updateOrderStatus(@PathVariable int id, @RequestBody OrderStatusRequest request) {
        Order existing = orders.get(id);
        if (existing == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Order " + id + " not found.");
        }
        Order updated = new Order(existing.id(), existing.customerId(), request.status(), existing.items(),
                existing.total(), existing.createdAt());
        return orders.save(updated);
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Void> deleteOrder(@PathVariable int id) {
        if (!orders.delete(id)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Order " + id + " not found.");
        }
        return ResponseEntity.noContent().build();
    }
}
