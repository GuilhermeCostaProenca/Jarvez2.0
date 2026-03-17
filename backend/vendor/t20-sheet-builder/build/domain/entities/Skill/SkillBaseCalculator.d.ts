import type { Attribute, Attributes } from '../Sheet/Attributes';
import type { Level } from '../Sheet/Level';
export type SkillBaseCalculatorInterface = {
    level: Level;
    attributes: Attributes;
    calculate(attribute: Attribute, isTrained: boolean): number;
};
export declare class SkillBaseCalculator implements SkillBaseCalculatorInterface {
    readonly level: Level;
    readonly attributes: Attributes;
    constructor(level: Level, attributes: Attributes);
    calculate(attribute: Attribute, isTrained: boolean): number;
}
