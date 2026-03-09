import { type Context } from '../Context';
import type { Attributes } from '../Sheet/Attributes';
import type { Level } from '../Sheet/Level';
import { SkillTotalCalculator } from './SkillTotalCalculator';
export declare class SkillTotalCalculatorFactory {
    static make(attributes: Attributes, level: Level, context: Context): SkillTotalCalculator;
}
