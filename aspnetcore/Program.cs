using Enlace.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Enlace: zero-config default — this app runs Swashbuckle conventionally, so
// AddEnlace() finds /swagger/v1/swagger.json with no options set.
builder.Services.AddEnlace();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// Enlace UI + resolved-spec endpoint, mounted at /enlace by default.
app.UseEnlace();

// ---------------------------------------------------------------------------
// Shared example API — see ../CONTRACT.md. In-memory only, resets on restart.
// Customers and Products are independent CRUDs; Orders references both, giving
// a workflow with real cross-node data to chain on the canvas.
// ---------------------------------------------------------------------------

var customers = new Dictionary<int, Customer>();
var nextCustomerId = 1;

var products = new Dictionary<int, Product>();
var nextProductId = 1;

var orders = new Dictionary<int, Order>();
var nextOrderId = 1;

// --- Customers ---------------------------------------------------------

app.MapGet("/customers", () => customers.Values)
    .WithName("ListCustomers").WithOpenApi();

app.MapGet("/customers/{id:int}", (int id) =>
    customers.TryGetValue(id, out var customer)
        ? Results.Ok(customer)
        : Results.NotFound(new ErrorResponse($"Customer {id} not found.")))
    .WithName("GetCustomer").WithOpenApi();

app.MapPost("/customers", (CustomerRequest request) =>
{
    var customer = new Customer(nextCustomerId++, request.Name, request.Email);
    customers[customer.Id] = customer;
    return Results.Created($"/customers/{customer.Id}", customer);
})
    .WithName("CreateCustomer").WithOpenApi();

app.MapPut("/customers/{id:int}", (int id, CustomerRequest request) =>
{
    if (!customers.ContainsKey(id))
    {
        return Results.NotFound(new ErrorResponse($"Customer {id} not found."));
    }

    var customer = new Customer(id, request.Name, request.Email);
    customers[id] = customer;
    return Results.Ok(customer);
})
    .WithName("UpdateCustomer").WithOpenApi();

app.MapDelete("/customers/{id:int}", (int id) =>
    customers.Remove(id) ? Results.NoContent() : Results.NotFound(new ErrorResponse($"Customer {id} not found.")))
    .WithName("DeleteCustomer").WithOpenApi();

// --- Products ------------------------------------------------------------

app.MapGet("/products", () => products.Values)
    .WithName("ListProducts").WithOpenApi();

app.MapGet("/products/{id:int}", (int id) =>
    products.TryGetValue(id, out var product)
        ? Results.Ok(product)
        : Results.NotFound(new ErrorResponse($"Product {id} not found.")))
    .WithName("GetProduct").WithOpenApi();

app.MapPost("/products", (ProductRequest request) =>
{
    var product = new Product(nextProductId++, request.Name, request.Price, request.Stock);
    products[product.Id] = product;
    return Results.Created($"/products/{product.Id}", product);
})
    .WithName("CreateProduct").WithOpenApi();

app.MapPut("/products/{id:int}", (int id, ProductRequest request) =>
{
    if (!products.ContainsKey(id))
    {
        return Results.NotFound(new ErrorResponse($"Product {id} not found."));
    }

    var product = new Product(id, request.Name, request.Price, request.Stock);
    products[id] = product;
    return Results.Ok(product);
})
    .WithName("UpdateProduct").WithOpenApi();

app.MapDelete("/products/{id:int}", (int id) =>
    products.Remove(id) ? Results.NoContent() : Results.NotFound(new ErrorResponse($"Product {id} not found.")))
    .WithName("DeleteProduct").WithOpenApi();

// --- Orders ----------------------------------------------------------------

app.MapGet("/orders", () => orders.Values)
    .WithName("ListOrders").WithOpenApi();

app.MapGet("/orders/{id:int}", (int id) =>
    orders.TryGetValue(id, out var order)
        ? Results.Ok(order)
        : Results.NotFound(new ErrorResponse($"Order {id} not found.")))
    .WithName("GetOrder").WithOpenApi();

app.MapPost("/orders", (OrderRequest request) =>
{
    if (!customers.ContainsKey(request.CustomerId))
    {
        return Results.BadRequest(new ErrorResponse($"customerId {request.CustomerId} does not exist."));
    }

    var items = new List<OrderItem>();
    foreach (var itemRequest in request.Items)
    {
        if (!products.TryGetValue(itemRequest.ProductId, out var product))
        {
            return Results.BadRequest(new ErrorResponse($"productId {itemRequest.ProductId} does not exist."));
        }

        items.Add(new OrderItem(itemRequest.ProductId, itemRequest.Quantity, product.Price));
    }

    var total = items.Sum(item => item.UnitPrice * item.Quantity);
    var order = new Order(nextOrderId++, request.CustomerId, "pending", items, total, DateTime.UtcNow);
    orders[order.Id] = order;
    return Results.Created($"/orders/{order.Id}", order);
})
    .WithName("CreateOrder").WithOpenApi();

app.MapPut("/orders/{id:int}/status", (int id, OrderStatusRequest request) =>
{
    if (!orders.TryGetValue(id, out var order))
    {
        return Results.NotFound(new ErrorResponse($"Order {id} not found."));
    }

    var updated = order with { Status = request.Status };
    orders[id] = updated;
    return Results.Ok(updated);
})
    .WithName("UpdateOrderStatus").WithOpenApi();

app.MapDelete("/orders/{id:int}", (int id) =>
    orders.Remove(id) ? Results.NoContent() : Results.NotFound(new ErrorResponse($"Order {id} not found.")))
    .WithName("DeleteOrder").WithOpenApi();

app.Run();

record Customer(int Id, string Name, string Email);
record CustomerRequest(string Name, string Email);

record Product(int Id, string Name, decimal Price, int Stock);
record ProductRequest(string Name, decimal Price, int Stock);

record OrderItem(int ProductId, int Quantity, decimal UnitPrice);
record OrderItemRequest(int ProductId, int Quantity);
record Order(int Id, int CustomerId, string Status, List<OrderItem> Items, decimal Total, DateTime CreatedAt);
record OrderRequest(int CustomerId, List<OrderItemRequest> Items);
record OrderStatusRequest(string Status);

record ErrorResponse(string Error);
