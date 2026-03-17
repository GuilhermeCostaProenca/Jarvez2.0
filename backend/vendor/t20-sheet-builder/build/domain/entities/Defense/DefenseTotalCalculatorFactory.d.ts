import type { Attributes } from '../Sheet/Attributes';
import { DefenseTotalCalculator } from './DefenseTotalCalculator';
export declare class DefenseTotalCalculatorFactory {
    static make(attributes: Attributes, armorBonus: number, shieldBonus: number): DefenseTotalCalculator;
}
