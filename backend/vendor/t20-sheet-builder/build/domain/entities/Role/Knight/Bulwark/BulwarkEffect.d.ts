import { TriggeredEffect, type TriggeredEffectModifiers } from '../../../Ability';
import { type TriggeredEffectActivation } from '../../../Ability/TriggeredEffectActivation';
import { type EnabledEffectModifiersIndexes } from '../../../Character/CharacterAttackTriggeredEffect';
import { ManaCost } from '../../../ManaCost';
import { type Cost } from '../../../Sheet';
export declare class BulwarkEffect extends TriggeredEffect {
    baseCosts: Cost[];
    description: string;
    constructor();
    enable({ modifiersIndexes, modifiers }: {
        modifiers: TriggeredEffectModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }, activation: TriggeredEffectActivation): {
        manaCost?: ManaCost | undefined;
    };
    disable({ modifiersIndexes, modifiers }: {
        modifiers: TriggeredEffectModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }): void;
}
