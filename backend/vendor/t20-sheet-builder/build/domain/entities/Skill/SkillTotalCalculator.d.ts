import type { ContextualModifiersListTotalCalculatorInterface } from '../Modifier/ContextualModifier/ContextualModifiersListTotalCalculator';
import type { FixedModifiersListTotalCalculatorInterface } from '../Modifier/FixedModifier/FixedModifiersListTotalCalculator';
import type { Skill } from './Skill';
import type { SkillBaseCalculatorInterface } from './SkillBaseCalculator';
export declare class SkillTotalCalculator {
    readonly baseCalculator: SkillBaseCalculatorInterface;
    readonly contextualCalculator: ContextualModifiersListTotalCalculatorInterface;
    readonly fixedCalculator: FixedModifiersListTotalCalculatorInterface;
    constructor(baseCalculator: SkillBaseCalculatorInterface, contextualCalculator: ContextualModifiersListTotalCalculatorInterface, fixedCalculator: FixedModifiersListTotalCalculatorInterface);
    calculate(skill: Skill): number;
}
