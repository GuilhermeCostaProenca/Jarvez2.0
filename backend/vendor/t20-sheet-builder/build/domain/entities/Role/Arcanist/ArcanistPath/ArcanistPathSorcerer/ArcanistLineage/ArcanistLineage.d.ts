import { type AbilityEffectsInterface } from '../../../../../Ability/AbilityEffects';
import { type AbilityLevel } from '../../../../../Ability/AbilityLevel';
import { type SerializedArcanistLineage } from '../../../SerializedArcanist';
import { type ArcanistLineageType } from './ArcanistLineageType';
export declare abstract class ArcanistLineage {
    abstract effects: Record<AbilityLevel, AbilityEffectsInterface>;
    abstract type: ArcanistLineageType;
    abstract serialize(): SerializedArcanistLineage;
}
