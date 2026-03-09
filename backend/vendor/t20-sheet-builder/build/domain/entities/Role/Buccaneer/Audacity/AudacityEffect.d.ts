import { TriggeredEffect, type TriggeredEffectModifiers } from '../../../Ability';
import { type AudacityActivation } from '../../../Ability/TriggeredEffectActivation';
import { type EnabledEffectModifiersIndexes } from '../../../Character/CharacterAttackTriggeredEffect';
import { ManaCost } from '../../../ManaCost';
import { type Cost } from '../../../Sheet';
export declare class AudacityEffect extends TriggeredEffect<AudacityActivation> {
    static cost: ManaCost;
    baseCosts: Cost[];
    description: string;
    constructor();
    enable({ modifiersIndexes, modifiers }: {
        modifiers: TriggeredEffectModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }, activation: AudacityActivation): {
        manaCost?: ManaCost | undefined;
    };
    disable({ modifiersIndexes, modifiers }: {
        modifiers: TriggeredEffectModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }): void;
}
