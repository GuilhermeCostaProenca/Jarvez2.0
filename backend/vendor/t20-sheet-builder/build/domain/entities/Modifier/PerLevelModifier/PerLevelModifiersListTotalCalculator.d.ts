import type { Attributes } from '../../Sheet/Attributes';
import type { Level } from '../../Sheet/Level';
import type { ModifiersListTotalCalculator } from '../ModifiersListInterface';
import type { PerLevelModifierInterface } from './PerLevelModifierInterface';
export type PerLevelModifiersListTotalCalculatorInterface = ModifiersListTotalCalculator<PerLevelModifierInterface>;
export declare class PerLevelModifiersListTotalCalculator implements PerLevelModifiersListTotalCalculatorInterface {
    readonly attributes: Attributes;
    readonly level: Level;
    constructor(attributes: Attributes, level: Level);
    calculate(modifiers: PerLevelModifierInterface[]): number;
}
