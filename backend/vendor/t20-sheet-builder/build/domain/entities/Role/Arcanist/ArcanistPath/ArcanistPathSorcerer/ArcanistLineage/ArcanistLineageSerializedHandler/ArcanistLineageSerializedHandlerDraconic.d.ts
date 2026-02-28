import { type SerializedArcanistLineage, type SerializedArcanistLineageDraconic } from '../../../../SerializedArcanist';
import { type ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageSerializedHandler } from './ArcanistLineageSerializedHandler';
export declare class ArcanistLineageSerializedHandlerDraconic extends ArcanistLineageSerializedHandler<SerializedArcanistLineageDraconic> {
    handle(request: SerializedArcanistLineageDraconic): ArcanistLineage;
    protected shouldHandle(request: SerializedArcanistLineage): boolean;
}
