import { ApiProperty } from '@nestjs/swagger';

// @nestjs/swagger introspects class metadata (via @ApiProperty), not plain
// TS interfaces, which don't exist at runtime — these classes are what the
// generated OpenAPI document's schemas come from.

export class CustomerRequest {
  @ApiProperty() name!: string;
  @ApiProperty() email!: string;
}

export class Customer extends CustomerRequest {
  @ApiProperty() id!: number;
}

export class ProductRequest {
  @ApiProperty() name!: string;
  @ApiProperty() price!: number;
  @ApiProperty() stock!: number;
}

export class Product extends ProductRequest {
  @ApiProperty() id!: number;
}

export class OrderItemRequest {
  @ApiProperty() productId!: number;
  @ApiProperty() quantity!: number;
}

export class OrderItem extends OrderItemRequest {
  @ApiProperty() unitPrice!: number;
}

export class OrderRequest {
  @ApiProperty() customerId!: number;
  @ApiProperty({ type: [OrderItemRequest] }) items!: OrderItemRequest[];
}

export class Order {
  @ApiProperty() id!: number;
  @ApiProperty() customerId!: number;
  @ApiProperty({ enum: ['pending', 'paid', 'shipped', 'cancelled'] }) status!: string;
  @ApiProperty({ type: [OrderItem] }) items!: OrderItem[];
  @ApiProperty() total!: number;
  @ApiProperty() createdAt!: string;
}

export class OrderStatusRequest {
  @ApiProperty({ enum: ['pending', 'paid', 'shipped', 'cancelled'] }) status!: string;
}

export class ErrorDto {
  @ApiProperty() error!: string;
}
