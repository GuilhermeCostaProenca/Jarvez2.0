import { type ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageHandler, type ArcanistLineageHandlerRequest } from './ArcanistLineageHandler';
export declare class ArcanistLineageFactoryHandlerDraconic extends ArcanistLineageHandler {
    protected handle(request: ArcanistLineageHandlerRequest): ArcanistLineage;
    protected shouldHandle(request: ArcanistLineageHandlerRequest): boolean;
}
