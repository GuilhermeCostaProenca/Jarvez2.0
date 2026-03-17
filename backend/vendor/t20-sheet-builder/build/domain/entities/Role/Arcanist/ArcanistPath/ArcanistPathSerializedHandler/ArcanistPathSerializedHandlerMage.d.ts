import { type ArcanistPath } from '..';
import { type SerializedArcanistPath, type SerializedArcanistMage } from '../../SerializedArcanist';
import { ArcanistPathSerializedHandler } from './ArcanistPathSerializedHandler';
export declare class ArcanistPathSerializedHandlerMage extends ArcanistPathSerializedHandler<SerializedArcanistMage> {
    protected handle(request: SerializedArcanistMage): ArcanistPath;
    protected shouldHandle(request: SerializedArcanistPath): boolean;
}
