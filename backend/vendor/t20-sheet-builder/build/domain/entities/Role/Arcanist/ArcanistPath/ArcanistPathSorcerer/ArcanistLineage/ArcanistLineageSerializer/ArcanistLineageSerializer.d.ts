import { type SerializedArcanistLineage } from '../../../../SerializedArcanist';
import { type ArcanistLineage } from '../ArcanistLineage';
export declare abstract class ArcanistLineageSerializer<L extends ArcanistLineage = ArcanistLineage, S extends SerializedArcanistLineage = SerializedArcanistLineage> {
    protected readonly lineage: L;
    constructor(lineage: L);
    abstract serialize(): S;
}
