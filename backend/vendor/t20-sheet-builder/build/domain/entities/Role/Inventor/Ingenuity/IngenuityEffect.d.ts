import { TriggeredEffect } from '../../../Ability';
import { type TriggeredEffectActivation } from '../../../Ability/TriggeredEffectActivation';
import { type CharacterModifierName } from '../../../Character';
import { ManaCost } from '../../../ManaCost';
import { type Modifiers } from '../../../Modifier';
import { type Cost } from '../../../Sheet';
export declare class IngenuityEffect extends TriggeredEffect {
    baseCosts: Cost[];
    description: string;
    constructor();
    enable({ modifiersIndexes, modifiers }: {
        modifiers: Partial<Record<CharacterModifierName, Modifiers>>;
        modifiersIndexes: Partial<Record<CharacterModifierName, number>>;
    }, activation: TriggeredEffectActivation): {
        manaCost?: ManaCost | undefined;
    };
    disable({ modifiersIndexes, modifiers }: {
        modifiers: Partial<Record<CharacterModifierName, Modifiers>>;
        modifiersIndexes: Partial<Record<CharacterModifierName, number>>;
    }): void;
}
