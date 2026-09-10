import { Body, Controller, Delete, Get, HttpCode, NotFoundException, Param, Post, Put } from '@nestjs/common';
import { ApiOperation, ApiParam, ApiResponse, ApiTags } from '@nestjs/swagger';
import { StoreService } from './store.service.js';
import { Customer, CustomerRequest, ErrorDto } from './dto.js';

@ApiTags('customers')
@Controller('customers')
export class CustomersController {
  constructor(private readonly store: StoreService) {}

  @Get()
  @ApiOperation({ operationId: 'listCustomers', summary: 'List customers' })
  @ApiResponse({ status: 200, description: 'Customers', type: [Customer] })
  list() {
    return [...this.store.customers.values()];
  }

  @Get(':id')
  @ApiOperation({ operationId: 'getCustomer', summary: 'Fetch a customer by id' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Customer found', type: Customer })
  @ApiResponse({ status: 404, description: 'Customer not found', type: ErrorDto })
  get(@Param('id') id: string) {
    const customer = this.store.customers.get(Number(id));
    if (!customer) throw new NotFoundException(`Customer ${id} not found.`);
    return customer;
  }

  @Post()
  @ApiOperation({ operationId: 'createCustomer', summary: 'Create a customer' })
  @ApiResponse({ status: 201, description: 'Customer created', type: Customer })
  create(@Body() body: CustomerRequest) {
    const customer = { id: this.store.nextId('customer'), name: body.name, email: body.email };
    this.store.customers.set(customer.id, customer);
    return customer;
  }

  @Put(':id')
  @ApiOperation({ operationId: 'updateCustomer', summary: 'Update a customer' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Customer updated', type: Customer })
  @ApiResponse({ status: 404, description: 'Customer not found', type: ErrorDto })
  update(@Param('id') id: string, @Body() body: CustomerRequest) {
    const numId = Number(id);
    if (!this.store.customers.has(numId)) throw new NotFoundException(`Customer ${id} not found.`);
    const customer = { id: numId, name: body.name, email: body.email };
    this.store.customers.set(numId, customer);
    return customer;
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ operationId: 'deleteCustomer', summary: 'Delete a customer' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 204, description: 'Customer deleted' })
  @ApiResponse({ status: 404, description: 'Customer not found', type: ErrorDto })
  remove(@Param('id') id: string) {
    if (!this.store.customers.delete(Number(id))) throw new NotFoundException(`Customer ${id} not found.`);
  }
}
