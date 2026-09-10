import { Body, Controller, Delete, Get, HttpCode, NotFoundException, Param, Post, Put } from '@nestjs/common';
import { ApiOperation, ApiParam, ApiResponse, ApiTags } from '@nestjs/swagger';
import { StoreService } from './store.service.js';
import { ErrorDto, Product, ProductRequest } from './dto.js';

@ApiTags('products')
@Controller('products')
export class ProductsController {
  constructor(private readonly store: StoreService) {}

  @Get()
  @ApiOperation({ operationId: 'listProducts', summary: 'List products' })
  @ApiResponse({ status: 200, description: 'Products', type: [Product] })
  list() {
    return [...this.store.products.values()];
  }

  @Get(':id')
  @ApiOperation({ operationId: 'getProduct', summary: 'Fetch a product by id' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Product found', type: Product })
  @ApiResponse({ status: 404, description: 'Product not found', type: ErrorDto })
  get(@Param('id') id: string) {
    const product = this.store.products.get(Number(id));
    if (!product) throw new NotFoundException(`Product ${id} not found.`);
    return product;
  }

  @Post()
  @ApiOperation({ operationId: 'createProduct', summary: 'Create a product' })
  @ApiResponse({ status: 201, description: 'Product created', type: Product })
  create(@Body() body: ProductRequest) {
    const product = { id: this.store.nextId('product'), name: body.name, price: body.price, stock: body.stock };
    this.store.products.set(product.id, product);
    return product;
  }

  @Put(':id')
  @ApiOperation({ operationId: 'updateProduct', summary: 'Update a product' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 200, description: 'Product updated', type: Product })
  @ApiResponse({ status: 404, description: 'Product not found', type: ErrorDto })
  update(@Param('id') id: string, @Body() body: ProductRequest) {
    const numId = Number(id);
    if (!this.store.products.has(numId)) throw new NotFoundException(`Product ${id} not found.`);
    const product = { id: numId, name: body.name, price: body.price, stock: body.stock };
    this.store.products.set(numId, product);
    return product;
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ operationId: 'deleteProduct', summary: 'Delete a product' })
  @ApiParam({ name: 'id', type: Number })
  @ApiResponse({ status: 204, description: 'Product deleted' })
  @ApiResponse({ status: 404, description: 'Product not found', type: ErrorDto })
  remove(@Param('id') id: string) {
    if (!this.store.products.delete(Number(id))) throw new NotFoundException(`Product ${id} not found.`);
  }
}
