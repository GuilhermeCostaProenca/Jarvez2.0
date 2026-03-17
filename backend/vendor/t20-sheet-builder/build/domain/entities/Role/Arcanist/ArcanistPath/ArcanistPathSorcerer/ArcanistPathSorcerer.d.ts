import { type AbilityEffectsInterface } from '../../../../Ability/AbilityEffects';
import { type Attributes } from '../../../../Sheet';
import { type SpellLearnFrequency } from '../../../SpellsAbility';
import { type SerializedArcanistPath } from '../../SerializedArcanist';
import { ArcanistPath, ArcanistPathName } from '../ArcanistPath';
import { type ArcanistLineage } from './ArcanistLineage/ArcanistLineage';
export declare class ArcanistPathSorcerer extends ArcanistPath {
    readonly lineage: ArcanistLineage;
    readonly pathName = ArcanistPathName.sorcerer;
    spellsAttribute: keyof Attributes;
    spellLearnFrequency: SpellLearnFrequency;
    effects: AbilityEffectsInterface;
    constructor(lineage: ArcanistLineage);
    serializePath(): SerializedArcanistPath;
}
