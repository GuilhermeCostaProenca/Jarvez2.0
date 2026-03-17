import { type ArcanistPathMage } from '..';
import { type SerializedArcanistMage } from '../../SerializedArcanist';
import { ArcanistPathSerializer } from './ArcanistPathSerializer';
export declare class ArcanistPathSerializerMage extends ArcanistPathSerializer<SerializedArcanistMage> {
    protected path: ArcanistPathMage;
    constructor(path: ArcanistPathMage);
    serialize(): SerializedArcanistMage;
}
