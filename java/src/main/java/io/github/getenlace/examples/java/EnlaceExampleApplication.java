package io.github.getenlace.examples.java;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Minimal Spring Boot app implementing the shared example contract (see ../../CONTRACT.md) —
 * in-memory Customers, Products, and Orders — wired up with enlace-java's
 * enlace-spring-boot-starter. Zero Enlace-specific config: adding the starter as a dependency
 * is enough, since this app already serves its OpenAPI document at springdoc's conventional
 * {@code /v3/api-docs}.
 */
@SpringBootApplication
public class EnlaceExampleApplication {

    public static void main(String[] args) {
        SpringApplication.run(EnlaceExampleApplication.class, args);
    }
}
