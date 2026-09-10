package io.github.getenlace.examples.java.customer;

import io.github.getenlace.examples.java.common.ApiException;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Collection;

// Without this, springdoc falls back to a tag derived from the class name
// ("customer-controller") — an implementation detail leaking into a user-facing grouping.
@Tag(name = "Customers")
@RestController
@RequestMapping("/customers")
class CustomerController {

    private final CustomerStore store;

    CustomerController(CustomerStore store) {
        this.store = store;
    }

    @GetMapping
    Collection<Customer> listCustomers() {
        return store.list();
    }

    @GetMapping("/{id}")
    Customer getCustomer(@PathVariable int id) {
        Customer customer = store.get(id);
        if (customer == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Customer " + id + " not found.");
        }
        return customer;
    }

    @PostMapping
    ResponseEntity<Customer> createCustomer(@RequestBody CustomerRequest request) {
        Customer customer = store.save(new Customer(store.nextId(), request.name(), request.email()));
        return ResponseEntity.status(HttpStatus.CREATED).body(customer);
    }

    @PutMapping("/{id}")
    Customer updateCustomer(@PathVariable int id, @RequestBody CustomerRequest request) {
        if (!store.exists(id)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Customer " + id + " not found.");
        }
        return store.save(new Customer(id, request.name(), request.email()));
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Void> deleteCustomer(@PathVariable int id) {
        if (!store.delete(id)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Customer " + id + " not found.");
        }
        return ResponseEntity.noContent().build();
    }
}
