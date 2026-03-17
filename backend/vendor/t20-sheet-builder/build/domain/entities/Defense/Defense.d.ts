import type { Attribute } from '../Sheet/Attributes';
import { FixedModifiersList } from '../Modifier/FixedModifier/FixedModifiersList';
import type { DefenseInterface } from './DefenseInterface';
import type { DefenseTotalCalculator } from './DefenseTotalCalculator';
import { type ModifierInterface } from '../Modifier/ModifierInterface';
export declare class Defense implements DefenseInterface {
    attribute: Attribute;
    readonly fixedModifiers: FixedModifiersList;
    addFixedModifier(modifier: ModifierInterface): void;
    getTotal(calculator: DefenseTotalCalculator): number;
}
