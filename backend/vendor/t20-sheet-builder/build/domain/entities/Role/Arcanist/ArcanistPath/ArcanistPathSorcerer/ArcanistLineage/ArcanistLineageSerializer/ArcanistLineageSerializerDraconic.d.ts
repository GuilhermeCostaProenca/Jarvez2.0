import { type SerializedArcanistLineageDraconic } from '../../../../SerializedArcanist';
import { type ArcanistLineageDraconic } from '../ArcanistLineageDraconic';
import { ArcanistLineageSerializer } from './ArcanistLineageSerializer';
export declare class ArcanistLineageSerializerDraconic extends ArcanistLineageSerializer<ArcanistLineageDraconic, SerializedArcanistLineageDraconic> {
    serialize(): SerializedArcanistLineageDraconic;
}
