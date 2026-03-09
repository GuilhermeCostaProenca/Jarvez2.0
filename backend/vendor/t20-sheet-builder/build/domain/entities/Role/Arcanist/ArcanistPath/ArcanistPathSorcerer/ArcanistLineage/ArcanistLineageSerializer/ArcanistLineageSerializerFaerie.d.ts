import { type SerializedArcanistLineageFaerie } from '../../../../SerializedArcanist';
import { type ArcanistLineageFaerie } from '../ArcanistLineageFaerie';
import { ArcanistLineageSerializer } from './ArcanistLineageSerializer';
export declare class ArcanistLineageSerializerFaerie extends ArcanistLineageSerializer<ArcanistLineageFaerie, SerializedArcanistLineageFaerie> {
    serialize(): SerializedArcanistLineageFaerie;
}
