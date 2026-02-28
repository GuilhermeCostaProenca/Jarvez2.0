import { type TriggeredEffect } from '../Ability';
import { type TriggeredEffectActivation } from '../Ability/TriggeredEffectActivation';
import { type EnabledEffectModifiersIndexes } from '../Character/CharacterAttackTriggeredEffect';
import { type ManaCost } from '../ManaCost';
import { type Modifiers } from '../Modifier';
export declare class CharacterSkillTriggeredEffect {
    readonly effect: TriggeredEffect;
    readonly modifiers: {
        skill: Modifiers;
        skillExceptAttack: Modifiers;
    };
    readonly modifiersIndexes: EnabledEffectModifiersIndexes;
    private isEnabled;
    private manaCost?;
    constructor(effect: TriggeredEffect, modifiers: {
        skill: Modifiers;
        skillExceptAttack: Modifiers;
    });
    enable(activation: TriggeredEffectActivation): void;
    disable(): void;
    getIsEnabled(): boolean;
    getManaCost(): ManaCost | undefined;
}
