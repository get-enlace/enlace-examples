import { Injectable } from '@nestjs/common';

// Shared example API — see ../../../CONTRACT.md. In-memory only, resets on
// restart. A dumb data store: existence checks and error shaping live in
// the controllers, matching how the express/dotnet examples structure it.

export interface Customer {
  id: number;
  name: string;
  email: string;
}

export interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
}

export interface OrderItem {
  productId: number;
  quantity: number;
  unitPrice: number;
}

export interface Order {
  id: number;
  customerId: number;
  status: string;
  items: OrderItem[];
  total: number;
  createdAt: string;
}

@Injectable()
export class StoreService {
  readonly customers = new Map<number, Customer>();
  private nextCustomerId = 1;

  readonly products = new Map<number, Product>();
  private nextProductId = 1;

  readonly orders = new Map<number, Order>();
  private nextOrderId = 1;

  nextId(resource: 'customer' | 'product' | 'order'): number {
    if (resource === 'customer') return this.nextCustomerId++;
    if (resource === 'product') return this.nextProductId++;
    return this.nextOrderId++;
  }
}
