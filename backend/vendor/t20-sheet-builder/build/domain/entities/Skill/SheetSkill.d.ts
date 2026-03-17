import { type TranslatableName } from '..';
import { type RollResult } from '../Dice';
import { DiceRoll } from '../Dice/DiceRoll';
import { Modifiers } from '../Modifier';
import { type RandomInterface } from '../Random';
import { type Attribute } from '../Sheet/Attributes';
import { type Skill } from './Skill';
import { type SkillName } from './SkillName';
import { type SkillTotalCalculator } from './SkillTotalCalculator';
export type SheetSkillsObject = Record<SkillName, SheetSkill>;
export type SkillRollResult = {
    roll: RollResult;
    modifiers: Modifiers;
    modifiersTotal: number;
    isCritical: boolean;
    isFumble: boolean;
    total: number;
    attributeModifier: number;
    levelPoints: number;
    trainingPoints: number;
};
export declare class SheetSkill {
    readonly skill: Skill;
    readonly calculator: SkillTotalCalculator;
    static test: DiceRoll;
    constructor(skill: Skill, calculator: SkillTotalCalculator);
    isTrained(): boolean;
    getName(): SkillName;
    getFixedModifier(name: TranslatableName): import("..").ModifierInterface | undefined;
    getContextualModifier(name: TranslatableName): import("..").ContextualModifierInterface | undefined;
    getModifiersTotal(): number;
    getAttributeModifier(): number;
    getLevelPoints(): number;
    getTrainingPoints(): number;
    getTotalBaseModifier(): number;
    changeAttribute(attribute: Attribute): void;
    roll(random?: RandomInterface, threat?: number): SkillRollResult;
}
