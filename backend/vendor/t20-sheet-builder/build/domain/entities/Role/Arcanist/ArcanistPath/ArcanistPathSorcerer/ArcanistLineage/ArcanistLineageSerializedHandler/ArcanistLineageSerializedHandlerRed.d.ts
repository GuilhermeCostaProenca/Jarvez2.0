import { type SerializedArcanistLineageRed } from '../../../../SerializedArcanist';
import { ArcanistLineageRed } from '../ArcanistLineageRed';
import { ArcanistLineageSerializedHandler } from './ArcanistLineageSerializedHandler';
export declare class ArcanistLineageSerializedHandlerRed extends ArcanistLineageSerializedHandler<SerializedArcanistLineageRed> {
    handle(request: SerializedArcanistLineageRed): ArcanistLineageRed;
    protected shouldHandle(request: SerializedArcanistLineageRed): boolean;
}
