import { AbilityEffects } from '../../../../Ability/AbilityEffects';
import { AbilityEffectsStatic } from '../../../../Ability/AbilityEffectsStatic';
import { type Character } from '../../../../Character';
import { CharacterAppliedFightStyle } from '../../../../Character/CharacterAppliedFightStyle';
import { type CharacterModifiers } from '../../../../Character/CharacterModifiers';
import { GeneralPowerName } from '../../GeneralPowerName';
import { FightStyle } from './FightStyle';
import { OneWeaponStyleEffect } from './OneWeaponStyleEffect';
export declare class OneWeaponStyle extends FightStyle {
    static readonly powerName = GeneralPowerName.oneWeaponStyle;
    static readonly effects: AbilityEffectsStatic;
    effects: AbilityEffects<{
        activateable: {
            default: OneWeaponStyleEffect;
        };
    }>;
    private readonly condition;
    constructor();
    applyModifiers(modifiers: CharacterModifiers): CharacterAppliedFightStyle;
    canActivate(character: Character): boolean;
}
