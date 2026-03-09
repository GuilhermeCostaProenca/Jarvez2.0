import { TriggeredEffect, type TriggeredEffectModifiers } from '../../../Ability/TriggeredEffect';
import { type SpecialAttackActivation } from '../../../Ability/TriggeredEffectActivation';
import { type EnabledEffectModifiersIndexes } from '../../../Character/CharacterAttackTriggeredEffect';
import { type CharacterAttackModifiers } from '../../../Character/CharactterAttackModifiers';
import { ManaCost } from '../../../ManaCost';
import { Level } from '../../../Sheet/Level';
import { SpecialAttackEffectCosts } from './SpecialAttackManaCost';
export declare class SpecialAttackEffect extends TriggeredEffect<SpecialAttackActivation> {
    get description(): string;
    static minLevelToCost: Record<SpecialAttackEffectCosts, Level>;
    static costs: Record<SpecialAttackEffectCosts, ManaCost>;
    static maxModifier: Record<SpecialAttackEffectCosts, number>;
    baseCosts: ManaCost[];
    constructor();
    enable({ modifiersIndexes, modifiers }: {
        modifiers: CharacterAttackModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }, activation: SpecialAttackActivation): {
        manaCost?: ManaCost;
    };
    disable({ modifiersIndexes, modifiers }: {
        modifiers: TriggeredEffectModifiers;
        modifiersIndexes: EnabledEffectModifiersIndexes;
    }): void;
    private enableAttackBonus;
    private enableDamageBonus;
    private enableSplittedBonus;
    private getBonusFromManaCost;
}
