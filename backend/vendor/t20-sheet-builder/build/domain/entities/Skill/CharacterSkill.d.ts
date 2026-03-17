import { type TranslatableName } from '..';
import { type TriggeredEffect, type TriggeredEffectName } from '../Ability';
import { type TriggeredEffectActivation } from '../Ability/TriggeredEffectActivation';
import { DiceRoll } from '../Dice/DiceRoll';
import { Modifiers, type ModifiersTotalCalculators } from '../Modifier';
import { type RandomInterface } from '../Random';
import { type Attribute } from '../Sheet/Attributes';
import { type SheetSkill, type SkillRollResult } from './SheetSkill';
import { CharacterSkillTriggeredEffect } from './CharacterSkillTriggeredEffect';
export declare class CharacterSkill {
    readonly sheetSkill: SheetSkill;
    readonly modifiers: {
        skill: Modifiers;
        skillExceptAttack: Modifiers;
    };
    readonly modifiersCalculators: ModifiersTotalCalculators;
    static test: DiceRoll;
    readonly triggeredEffects: Map<TriggeredEffectName, CharacterSkillTriggeredEffect>;
    constructor(sheetSkill: SheetSkill, modifiers: {
        skill: Modifiers;
        skillExceptAttack: Modifiers;
    }, triggeredEffects: Map<TriggeredEffectName, TriggeredEffect>, modifiersCalculators: ModifiersTotalCalculators);
    getName(): import("./SkillName").SkillName;
    enableTriggeredEffect(activation: TriggeredEffectActivation): void;
    disableTriggeredEffect(effectName: TriggeredEffectName): void;
    getModifiersTotal(isAttack?: boolean): number;
    getAttributeModifier(): number;
    getLevelPoints(): number;
    getTrainingPoints(): number;
    getTotalBaseModifier(): number;
    changeAttribute(attribute: Attribute): void;
    getTriggeredEffects(): Map<TriggeredEffectName, CharacterSkillTriggeredEffect>;
    getFixedModifier(type: keyof CharacterSkill['modifiers'], name: TranslatableName): import("..").ModifierInterface | undefined;
    getContextualModifier(name: TranslatableName): import("..").ContextualModifierInterface | undefined;
    roll(random?: RandomInterface, threat?: number, isAttack?: boolean): SkillRollResult;
}
