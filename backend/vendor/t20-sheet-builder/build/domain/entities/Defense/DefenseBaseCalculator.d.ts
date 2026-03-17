import type { Attribute, Attributes } from '../Sheet/Attributes';
export declare class DefenseBaseCalculator {
    readonly attributes: Attributes;
    readonly armorBonus: number;
    readonly shieldBonus: number;
    private static get initialValue();
    constructor(attributes: Attributes, armorBonus: number, shieldBonus: number);
    calculate(attribute: Attribute): number;
}
