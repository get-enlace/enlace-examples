package io.github.getenlace.examples.java.product;

import io.github.getenlace.examples.java.common.ApiException;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Collection;

// Without this, springdoc falls back to a tag derived from the class name
// ("product-controller") — an implementation detail leaking into a user-facing grouping.
@Tag(name = "Products")
@RestController
@RequestMapping("/products")
class ProductController {

    private final ProductStore store;

    ProductController(ProductStore store) {
        this.store = store;
    }

    @GetMapping
    Collection<Product> listProducts() {
        return store.list();
    }

    @GetMapping("/{id}")
    Product getProduct(@PathVariable int id) {
        Product product = store.get(id);
        if (product == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Product " + id + " not found.");
        }
        return product;
    }

    @PostMapping
    ResponseEntity<Product> createProduct(@RequestBody ProductRequest request) {
        Product product = store.save(new Product(store.nextId(), request.name(), request.price(), request.stock()));
        return ResponseEntity.status(HttpStatus.CREATED).body(product);
    }

    @PutMapping("/{id}")
    Product updateProduct(@PathVariable int id, @RequestBody ProductRequest request) {
        if (!store.exists(id)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Product " + id + " not found.");
        }
        return store.save(new Product(id, request.name(), request.price(), request.stock()));
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Void> deleteProduct(@PathVariable int id) {
        if (!store.delete(id)) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Product " + id + " not found.");
        }
        return ResponseEntity.noContent().build();
    }
}
