import { Module } from '@nestjs/common';
import { EnlaceModule } from '@get-enlace/nest';
import { ResourcesModule } from './resources.module.js';

@Module({
  imports: [EnlaceModule, ResourcesModule],
})
export class AppModule {}
