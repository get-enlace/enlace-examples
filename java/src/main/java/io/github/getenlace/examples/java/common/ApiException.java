package io.github.getenlace.examples.java.common;

import org.springframework.http.HttpStatus;

/**
 * Thrown for any contract-defined error response — see the shared example contract
 * (CONTRACT.md, at the enlace-examples repo root) for the error shape. Public: every
 * feature package's controller throws this.
 */
public class ApiException extends RuntimeException {

    private final HttpStatus status;

    public ApiException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }
}
