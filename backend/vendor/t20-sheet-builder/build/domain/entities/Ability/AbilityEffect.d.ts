import { type SerializedSheetAbilityEffect } from '..';
import type { AbilityName } from './Ability';
export type EffectType = 'active' | 'passive' | 'roleplay';
export type AbilityEffectInterface = {
    type: EffectType;
    source: AbilityName;
    readonly description: string;
    serialize(): SerializedSheetAbilityEffect;
};
export declare abstract class AbilityEffect implements AbilityEffectInterface {
    readonly type: EffectType;
    readonly source: AbilityName;
    abstract readonly description: string;
    constructor(type: EffectType, source: AbilityName);
    serialize(): SerializedSheetAbilityEffect;
}
