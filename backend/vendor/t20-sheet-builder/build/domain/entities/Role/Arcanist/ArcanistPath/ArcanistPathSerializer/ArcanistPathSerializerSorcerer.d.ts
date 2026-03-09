import { type SerializedArcanistSorcerer } from '../../SerializedArcanist';
import { type ArcanistPathSorcerer } from '../ArcanistPathSorcerer';
import { ArcanistPathSerializer } from './ArcanistPathSerializer';
export declare class ArcanistPathSerializerSorcerer extends ArcanistPathSerializer<SerializedArcanistSorcerer> {
    private readonly path;
    private readonly lineageSerializer;
    constructor(path: ArcanistPathSorcerer);
    serialize(): SerializedArcanistSorcerer;
    private getLineageSerializer;
}
