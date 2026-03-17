import { RoleSerializer } from '../../RoleSerializer';
import { type Arcanist } from '../Arcanist';
import { type SerializedArcanist } from '../SerializedArcanist';
/**
* @deprecated Use `arcanist.serialize()` instead
*/
export declare class ArcanistSerializer extends RoleSerializer<SerializedArcanist> {
    private readonly arcanist;
    private readonly pathSerializer;
    constructor(arcanist: Arcanist);
    protected serializeRole(): SerializedArcanist;
    private getPathSerializer;
}
