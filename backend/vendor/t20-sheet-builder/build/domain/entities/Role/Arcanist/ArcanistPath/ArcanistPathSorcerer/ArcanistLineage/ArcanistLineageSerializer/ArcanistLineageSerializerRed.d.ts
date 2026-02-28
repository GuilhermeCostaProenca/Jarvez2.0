import { type SerializedArcanistLineageRed } from '../../../../SerializedArcanist';
import { type ArcanistLineageRed } from '../ArcanistLineageRed';
import { ArcanistLineageSerializer } from './ArcanistLineageSerializer';
export declare class ArcanistLineageSerializerRed extends ArcanistLineageSerializer<ArcanistLineageRed, SerializedArcanistLineageRed> {
    serialize(): SerializedArcanistLineageRed;
}
