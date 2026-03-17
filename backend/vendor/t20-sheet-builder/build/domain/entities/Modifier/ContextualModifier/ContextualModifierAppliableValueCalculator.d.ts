import { type ContextualModifierInterface } from '.';
import { type Context } from '../../Context';
import type { Attribute, Attributes } from '../../Sheet/Attributes';
import type { ModifierAppliableValueCalculatorInterface } from '../ModifierInterface';
import { ModifierAppliableValueCalculator } from '../ModifierValueGetter';
export declare class ContextualModifierAppliableValueCalculator extends ModifierAppliableValueCalculator implements ModifierAppliableValueCalculatorInterface {
    readonly context: Context;
    readonly modifier: ContextualModifierInterface;
    constructor(attributes: Attributes, context: Context, modifier: ContextualModifierInterface);
    calculate(value: number, attributes: Attribute[]): number;
}
