import { type Context } from '../../Context';
import type { Attributes } from '../../Sheet/Attributes';
import type { ModifiersListTotalCalculator } from '../ModifiersListInterface';
import type { ContextualModifierInterface } from './ContextualModifierInterface';
export type ContextualModifiersListTotalCalculatorInterface = ModifiersListTotalCalculator<ContextualModifierInterface>;
export declare class ContextualModifiersListTotalCalculator implements ContextualModifiersListTotalCalculatorInterface {
    readonly context: Context;
    readonly attributes: Attributes;
    constructor(context: Context, attributes: Attributes);
    calculate(modifiers: ContextualModifierInterface[]): number;
}
