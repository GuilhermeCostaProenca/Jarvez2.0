import { type ArcanistPath } from '..';
import { type SerializedArcanistWizard } from '../../SerializedArcanist';
import { ArcanistPathSerializedHandler } from './ArcanistPathSerializedHandler';
export declare class ArcanistPathSerializedHandlerWizard extends ArcanistPathSerializedHandler<SerializedArcanistWizard> {
    protected handle(request: SerializedArcanistWizard): ArcanistPath;
    protected shouldHandle(request: SerializedArcanistWizard): boolean;
}
