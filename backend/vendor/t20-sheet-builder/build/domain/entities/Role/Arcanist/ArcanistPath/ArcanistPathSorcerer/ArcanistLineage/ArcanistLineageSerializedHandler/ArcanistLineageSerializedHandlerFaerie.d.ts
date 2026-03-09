import { type SerializedArcanistLineageFaerie } from '../../../../SerializedArcanist';
import { type ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageSerializedHandler } from './ArcanistLineageSerializedHandler';
export declare class ArcanistLineageSerializedHandlerFaerie extends ArcanistLineageSerializedHandler<SerializedArcanistLineageFaerie> {
    handle(request: SerializedArcanistLineageFaerie): ArcanistLineage;
    protected shouldHandle(request: SerializedArcanistLineageFaerie): boolean;
}
