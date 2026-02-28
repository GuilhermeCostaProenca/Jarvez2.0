import { type Context } from '../Context';
import { type ContextualModifierInterface } from '../Modifier/ContextualModifier/ContextualModifierInterface';
import { ContextualModifiersList } from '../Modifier/ContextualModifier/ContextualModifierList';
import { type FixedModifierInterface } from '../Modifier/FixedModifier/FixedModifier';
import { FixedModifiersList } from '../Modifier/FixedModifier/FixedModifiersList';
import { type SerializedSheetSkill } from '../Sheet';
import type { Attribute, Attributes } from '../Sheet/Attributes';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { type SkillName } from './SkillName';
import type { SkillTotalCalculator } from './SkillTotalCalculator';
export type SkillParams = {
    attribute: Attribute;
    isTrained?: boolean;
    name: SkillName;
};
export declare class Skill {
    static calculateTrainedPoints(level?: number): 2 | 4 | 6;
    static calculateTrainingPoints(level?: number, isTrained?: boolean): 0 | 2 | 4 | 6;
    static calculateLevelPoints(level: number): number;
    attribute: Attribute;
    readonly name: SkillName;
    readonly defaultAttribute: Attribute;
    readonly contextualModifiers: ContextualModifiersList;
    readonly fixedModifiers: FixedModifiersList;
    private isTrained;
    static get repeatedOtherModifierError(): string;
    constructor(params: SkillParams);
    changeAttribute(attribute: Attribute): void;
    addContextualModifier(modifier: ContextualModifierInterface): void;
    addFixedModifier(modifier: FixedModifierInterface): void;
    train(): void;
    getIsTrained(): boolean;
    getTotal(calculator: SkillTotalCalculator): number;
    getTrainingPoints(level?: number): 0 | 2 | 4 | 6;
    getLevelPoints(level?: number): number;
    getAttributeModifier(attributes: Attributes): number;
    serialize(totalCalculator: SkillTotalCalculator, sheet: SheetInterface, context: Context): SerializedSheetSkill;
}
