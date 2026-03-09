import { ArcanistLineageRed } from '../ArcanistLineageRed';
import { ArcanistLineageHandler, type ArcanistLineageHandlerRequest } from './ArcanistLineageHandler';
export declare class ArcanistLineageFactoryHandlerRed extends ArcanistLineageHandler {
    protected handle(request: ArcanistLineageHandlerRequest): ArcanistLineageRed;
    protected shouldHandle(request: ArcanistLineageHandlerRequest): boolean;
}
