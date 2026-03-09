import type { FixedModifierInterface } from '../Modifier/FixedModifier/FixedModifier';
import type { FixedModifiersListInterface } from '../Modifier/FixedModifier/FixedModifiersList';
import type { PerLevelModifierInterface } from '../Modifier/PerLevelModifier/PerLevelModifierInterface';
import { PerLevelModifiersList } from '../Modifier/PerLevelModifier/PerLevelModifiersList';
import type { PointsInterface } from './PointsInterface';
import type { PointsMaxCalculatorInterface } from './PointsMaxCalculator';
export declare abstract class Points implements PointsInterface {
    readonly type: 'mana' | 'life';
    readonly fixedModifiers: FixedModifiersListInterface;
    readonly perLevelModifiers: PerLevelModifiersList;
    constructor(type: 'mana' | 'life');
    addModifier(modifier: FixedModifierInterface): void;
    addPerLevelModifier(modifier: PerLevelModifierInterface): void;
    getMax(calculator: PointsMaxCalculatorInterface): number;
}
