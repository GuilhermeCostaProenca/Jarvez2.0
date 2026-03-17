import type { Attribute, Attributes } from '../../Sheet/Attributes';
import type { Level } from '../../Sheet/Level';
import type { ModifierAppliableValueCalculatorInterface } from '../ModifierInterface';
import { ModifierAppliableValueCalculator } from '../ModifierValueGetter';
import { type PerLevelModifierInterface } from './PerLevelModifierInterface';
export declare class PerLevelModifierAppliableValueCalculator extends ModifierAppliableValueCalculator implements ModifierAppliableValueCalculatorInterface {
    readonly level: Level;
    readonly modifier: PerLevelModifierInterface;
    constructor(attributes: Attributes, level: Level, modifier: PerLevelModifierInterface);
    calculate(value: number, attributes: Attribute[]): number;
}
