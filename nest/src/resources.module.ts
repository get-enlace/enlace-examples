import { Module } from '@nestjs/common';
import { StoreService } from './store.service.js';
import { CustomersController } from './customers.controller.js';
import { ProductsController } from './products.controller.js';
import { OrdersController } from './orders.controller.js';

// Isolated from AppModule specifically so main.ts's SwaggerModule.createDocument
// can scope generation to `include: [ResourcesModule]` — otherwise it scans
// the whole app, including @get-enlace/nest's own EnlaceController, and the
// generated spec ends up with a spurious "GET /enlace/api/spec" operation
// alongside the real business ones.
@Module({
  controllers: [CustomersController, ProductsController, OrdersController],
  providers: [StoreService],
})
export class ResourcesModule {}
