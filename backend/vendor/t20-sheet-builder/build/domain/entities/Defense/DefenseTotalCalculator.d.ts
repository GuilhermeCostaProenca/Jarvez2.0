import type { Attribute } from '../Sheet/Attributes';
import type { FixedModifiersList } from '../Modifier/FixedModifier/FixedModifiersList';
import type { FixedModifiersListTotalCalculatorInterface } from '../Modifier/FixedModifier/FixedModifiersListTotalCalculator';
import type { DefenseBaseCalculator } from './DefenseBaseCalculator';
export declare class DefenseTotalCalculator {
    readonly baseCalculator: DefenseBaseCalculator;
    readonly fixedCalculator: FixedModifiersListTotalCalculatorInterface;
    constructor(baseCalculator: DefenseBaseCalculator, fixedCalculator: FixedModifiersListTotalCalculatorInterface);
    calculate(attribute: Attribute, fixedModifiers: FixedModifiersList): number;
}
