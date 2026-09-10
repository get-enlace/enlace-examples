import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { EnlaceModule } from '@get-enlace/nest';
import { AppModule } from './app.module.js';
import { ContractErrorFilter } from './contract-error.filter.js';
import { ResourcesModule } from './resources.module.js';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalFilters(new ContractErrorFilter());

  const port = process.env.PORT ?? 4000;

  const config = new DocumentBuilder()
    .setTitle('Enlace Example API (NestJS)')
    .setVersion('1.0.0')
    // Enlace's chain executor reads servers[0].url to know where to send
    // the actual HTTP requests — see ARCHITECTURE.md §3/§6.
    .addServer(`http://localhost:${port}`)
    .build();

  // One call: generate the spec from decorators and hand it to Enlace.
  // include: [ResourcesModule] scopes generation to business controllers
  // only — without it, @get-enlace/nest's own EnlaceController would
  // appear as a spurious "GET /enlace/api/spec" operation in the spec.
  EnlaceModule.setSpec(app, SwaggerModule.createDocument(app, config, { include: [ResourcesModule] }));

  await app.listen(port);
  console.log(`Enlace example (NestJS) running at http://localhost:${port}`);
  console.log(`  Canvas:  http://localhost:${port}/enlace`);
  console.log(`  Spec:    http://localhost:${port}/enlace/api/spec`);
}

bootstrap();
