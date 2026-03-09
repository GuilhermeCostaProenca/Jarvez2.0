import type { Attribute, Attributes } from '../Sheet/Attributes';
import type { ModifierAppliableValueCalculatorInterface } from './ModifierInterface';
export declare abstract class ModifierAppliableValueCalculator implements ModifierAppliableValueCalculatorInterface {
    readonly attributes: Attributes;
    constructor(attributes: Attributes);
    abstract calculate(baseValue: number, attributeBonuses: Attribute[]): number;
    protected getAttributesBonusesTotal(attributeBonuses: Attribute[]): number;
}
