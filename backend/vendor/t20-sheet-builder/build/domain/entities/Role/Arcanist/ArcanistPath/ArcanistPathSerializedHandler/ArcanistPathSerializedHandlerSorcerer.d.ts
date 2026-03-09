import { type SerializedArcanistSorcerer } from '../../SerializedArcanist';
import { type ArcanistPath } from '../ArcanistPath';
import { ArcanistPathSerializedHandler } from './ArcanistPathSerializedHandler';
export declare class ArcanistPathSerializedHandlerSorcerer extends ArcanistPathSerializedHandler<SerializedArcanistSorcerer> {
    protected handle(request: SerializedArcanistSorcerer): ArcanistPath;
    protected shouldHandle(request: SerializedArcanistSorcerer): boolean;
}
