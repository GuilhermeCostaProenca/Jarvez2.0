import { type ArcanistPath } from '../ArcanistPath';
import { ArcanistPathHandler, type ArcanistPathHandlerRequest } from './ArcanistPathHandler';
export declare class ArcanistPathHandlerMage extends ArcanistPathHandler {
    handle(request: ArcanistPathHandlerRequest): ArcanistPath;
    protected shouldHandle(request: ArcanistPathHandlerRequest): boolean;
}
