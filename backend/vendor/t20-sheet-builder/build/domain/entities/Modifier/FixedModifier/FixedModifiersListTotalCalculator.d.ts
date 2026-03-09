import type { Attributes } from '../../Sheet/Attributes';
import type { FixedModifierInterface } from './FixedModifier';
import type { ModifiersListTotalCalculator } from '../ModifiersListInterface';
export type FixedModifiersListTotalCalculatorInterface = ModifiersListTotalCalculator<FixedModifierInterface>;
export declare class FixedModifiersListTotalCalculator implements FixedModifiersListTotalCalculatorInterface {
    readonly attributes: Attributes;
    constructor(attributes: Attributes);
    calculate(modifiers: FixedModifierInterface[]): number;
}
