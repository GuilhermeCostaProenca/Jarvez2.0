import type { Attribute } from '../../../Sheet';
import { RoleAbility } from '../../RoleAbility';
import type { SpellLearnFrequency } from '../../SpellsAbility';
import { type SerializedArcanistPath } from '../SerializedArcanist';
export declare enum ArcanistPathName {
    wizard = "wizard",
    sorcerer = "sorcerer",
    mage = "mage"
}
export declare abstract class ArcanistPath extends RoleAbility {
    abstract pathName: ArcanistPathName;
    abstract spellsAttribute: Attribute;
    abstract spellLearnFrequency: SpellLearnFrequency;
    constructor();
    abstract serializePath(): SerializedArcanistPath;
}
