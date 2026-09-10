import { BadRequestException, Body, Controller, Delete, Get, HttpCode, NotFoundException, Param, Post, Put } from '@nestjs/common';
import { ApiOperation, ApiParam, ApiResponse, ApiTags } from '@nestjs/swagger';
import { StoreService } from './store.service.js';
import { ErrorDto, Order, OrderRequest, OrderStatusRequest } from './dto.js';

@ApiTags('orders')
@Controller('orders')
export class OrdersController {
  constructor(private readonly store: StoreService) {}

  @Get()
  @ApiOperation({ operationId: 'listOrders', summary: 'List orders' })
  @ApiResponse({ status: 200, description: 'Orders', type: [Order] })
  list() {
    return [...this.store.orders.values()];
  }

  @Get(':id')
  @ApiOperation({ operationId: 'getOrder', summary: 'Fetch an order by id' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Order found', type: Order })
  @ApiResponse({ status: 404, description: 'Order not found', type: ErrorDto })
  get(@Param('id') id: string) {
    const order = this.store.orders.get(Number(id));
    if (!order) throw new NotFoundException(`Order ${id} not found.`);
    return order;
  }

  @Post()
  @ApiOperation({ operationId: 'createOrder', summary: 'Create an order (references an existing customer + products)' })
  @ApiResponse({ status: 201, description: 'Order created', type: Order })
  @ApiResponse({ status: 400, description: 'Unknown customerId or productId', type: ErrorDto })
  create(@Body() body: OrderRequest) {
    if (!this.store.customers.has(body.customerId)) {
      throw new BadRequestException(`customerId ${body.customerId} does not exist.`);
    }

    const items = body.items.map((item) => {
      const product = this.store.products.get(item.productId);
      if (!product) throw new BadRequestException(`productId ${item.productId} does not exist.`);
      return { productId: item.productId, quantity: item.quantity, unitPrice: product.price };
    });

    const total = items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);
    const order = {
      id: this.store.nextId('order'),
      customerId: body.customerId,
      status: 'pending',
      items,
      total,
      createdAt: new Date().toISOString(),
    };
    this.store.orders.set(order.id, order);
    return order;
  }

  @Put(':id/status')
  @ApiOperation({ operationId: 'updateOrderStatus', summary: "Update an order's status" })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Order updated', type: Order })
  @ApiResponse({ status: 404, description: 'Order not found', type: ErrorDto })
  updateStatus(@Param('id') id: string, @Body() body: OrderStatusRequest) {
    const numId = Number(id);
    const order = this.store.orders.get(numId);
    if (!order) throw new NotFoundException(`Order ${id} not found.`);
    const updated = { ...order, status: body.status };
    this.store.orders.set(numId, updated);
    return updated;
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ operationId: 'deleteOrder', summary: 'Delete an order' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 204, description: 'Order deleted' })
  @ApiResponse({ status: 404, description: 'Order not found', type: ErrorDto })
  remove(@Param('id') id: string) {
    if (!this.store.orders.delete(Number(id))) throw new NotFoundException(`Order ${id} not found.`);
  }
}
